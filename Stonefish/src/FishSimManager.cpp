#include "FishSimManager.h"

#include <Stonefish/actuators/Motor.h>
#include <Stonefish/actuators/VariableBuoyancy.h>
#include <Stonefish/core/Console.h>
#include <Stonefish/core/FeatherstoneRobot.h>
#include <Stonefish/core/ScenarioParser.h>
#include <Stonefish/core/SimulationApp.h>
#include <Stonefish/entities/SolidEntity.h>
#include <Stonefish/entities/forcefields/Ocean.h>
#include <Stonefish/sensors/scalar/IMU.h>
#include <Stonefish/sensors/scalar/Pressure.h>
#include <Stonefish/sensors/scalar/RotaryEncoder.h>
#include <Stonefish/utils/SystemUtil.hpp>

#include <cmath>
#include <cstdio>
#include <sstream>
#include <stdexcept>

namespace fish
{
    static const char* ROBOT = "Fish";

    FishSimManager::FishSimManager(const Config& cfg)
        : sf::SimulationManager(cfg.d("sim", "steps_per_second")), cfg_(cfg)
    {
        setRealtimeFactor(cfg_.d("sim", "realtime_factor"));
        logEvery_ = cfg_.at("log").at("every_n_steps").get<int>();
    }

    FishSimManager::~FishSimManager() = default;

    // ================================================================== budowa sceny

    void FishSimManager::BuildScenario()
    {
        // Grawitację można wyłączyć (test napędu wewnętrznego) – domyślnie 9.81 m/s².
        // Musi być TUTAJ, nie w konstruktorze: biblioteka ustawia g = 9.81 w InitializeSolver(),
        // wywoływanym po konstruktorze, a przed BuildScenario(). Przed parserem, bo VBS
        // zapamiętuje g w chwili tworzenia.
        if(cfg_.at("sim").contains("gravity"))
            setGravity(cfg_.d("sim", "gravity"));

        // 1) Scenariusz z XML (ścieżki w XML są względne do katalogu data/)
        const std::string scn = sf::GetDataPath() + "scenarios/" + cfg_.s("sim", "scenario");
        sf::ScenarioParser parser(this);
        parsedOk_ = parser.Parse(scn);
        for(const auto& m : parser.getLog())
        {
            // komunikaty parsera przekazujemy do konsoli Stonefish (widać je też w GUI, klawisz C)
            switch(m.type)
            {
                case sf::MessageType::INFO: cInfo("%s", m.text.c_str()); break;
                case sf::MessageType::WARNING: cWarning("%s", m.text.c_str()); break;
                case sf::MessageType::ERROR: cError("%s", m.text.c_str()); break;
                case sf::MessageType::CRITICAL: cError("%s", m.text.c_str()); break;
            }
        }
        if(!parsedOk_)
        {
            cError("Błędy parsera w scenariuszu '%s'!", scn.c_str());
            return;
        }

        // 2) Prądy morskie: parser dodaje <current> do oceanu, ale w Stonefish 1.5 są one
        //    domyślnie WYŁĄCZONE (Ocean::currentsEnabled = false) i trzeba je włączyć w kodzie –
        //    tak robią też przykłady biblioteki (Tests/UnderwaterTest). Bez prądów nic to nie zmienia.
        if(getOcean() != nullptr && getOcean()->getCurrent(0) != nullptr)
            getOcean()->EnableCurrents();

        // 3) Hydrodynamika w każdym kroku (domyślnie Stonefish liczy ją z częstotliwością 50 Hz)
        setFluidDynamicsPrescaler(cfg_.at("sim").at("fluid_prescaler").get<unsigned int>());

        FindRobotParts();
        ResetControl();
        BuildMassReport();
        cInfo("%s", massReport_.c_str());
    }

    void FishSimManager::FindRobotParts()
    {
        robot_ = dynamic_cast<sf::FeatherstoneRobot*>(getRobot(ROBOT));
        if(robot_ == nullptr)
            throw std::runtime_error("W scenariuszu nie ma robota 'Fish'");

        const std::string p = std::string(ROBOT) + "/";
        links_.clear();
        links_.push_back(robot_->getLink(p + "Head"));
        const int nSeg = cfg_.at("geometry").at("n_segments").get<int>();
        for(int i = 1; i <= nSeg; ++i)
            links_.push_back(robot_->getLink(p + "Seg" + std::to_string(i)));
        links_.push_back(robot_->getLink(p + "Fin"));
        for(auto* l : links_)
            if(l == nullptr) throw std::runtime_error("Brak ogniwa ryby w scenariuszu");
        allLinks_ = links_;

        motors_.clear();
        encoders_.clear();
        for(int i = 1; i <= nSeg; ++i)
        {
            auto* m = dynamic_cast<sf::Motor*>(robot_->getActuator(p + "TailM" + std::to_string(i)));
            auto* e = dynamic_cast<sf::RotaryEncoder*>(robot_->getSensor(p + "Enc" + std::to_string(i)));
            if(m == nullptr || e == nullptr)
                throw std::runtime_error("Brak aktuatora TailM" + std::to_string(i) + " albo enkodera Enc" + std::to_string(i));
            motors_.push_back(m);
            encoders_.push_back(e);
        }
        vbs_ = dynamic_cast<sf::VariableBuoyancy*>(robot_->getActuator(p + "VBS"));
        pressure_ = dynamic_cast<sf::Pressure*>(robot_->getSensor(p + "Pressure"));
        imu_ = dynamic_cast<sf::IMU*>(robot_->getSensor(p + "IMU"));
        if(vbs_ == nullptr || pressure_ == nullptr || imu_ == nullptr)
            throw std::runtime_error("Brak VBS, czujnika ciśnienia albo IMU w scenariuszu");

        // Siła nośna płetwy – własny aktuator przyczepiony do ogniwa "Fin" (src/FinLift.h).
        // Robot jest już w symulacji, więc dołączamy go ręcznie: AttachToSolid + AddActuator.
        finLift_ = nullptr;
        if(cfg_.b("fin_lift", "enabled"))
        {
            const auto fin = cfg_.at("geometry").at("fin_semi_axes").get<std::vector<double>>();
            const double area = M_PI * fin[0] * fin[2];                                   // rzut boczny (XZ)
            const double xc = -fin[0] + cfg_.d("geometry", "segment_overlap");          // środek płetwy w jej układzie
            finLift_ = new FinLift(p + "FinLift", area, cfg_.d("fin_lift", "cl_alpha"));
            finLift_->AttachToSolid(links_.back(), sf::Transform(sf::IQ(), sf::Vector3(xc, 0, 0)));
            AddActuator(finLift_);
        }

        ApplySkinFriction();

        theta_.assign(nSeg, 0.0);
        omega_.assign(nSeg, 0.0);
        tau_.assign(nSeg, 0.0);
    }

    // Bilans mas WYLICZONY PRZEZ STONEFISH z siatek i gęstości (porównaj z tools/make_meshes.py).
    void FishSimManager::BuildMassReport()
    {
        const double rho = cfg_.d("materials", "rho_water");
        const double g = std::fabs(getGravity().getZ()) > 0 ? std::fabs(getGravity().getZ()) : 9.81;
        std::ostringstream os;
        char buf[256];
        os << "Bilans mas (wartości policzone przez Stonefish z siatek):\n";
        std::snprintf(buf, sizeof(buf), "  %-6s %9s %9s %26s %26s\n", "bryła", "masa[g]", "V[ml]",
                      "masa doł. x,y,z [g]", "bezwł. doł. x,y,z [kg·cm²]");
        os << buf;
        double M = 0.0, V = 0.0;
        for(auto* l : allLinks_)
        {
            const std::string name = l->getName().substr(std::string(ROBOT).size() + 1);
            // getVolume() – objętość wypierająca wodę (dla bryły złożonej: części z buoyant="true")
            const sf::Vector3 am = l->getAddedMass(), ai = l->getAddedInertia();
            std::snprintf(buf, sizeof(buf), "  %-6s %9.1f %9.1f %8.1f %8.1f %8.1f %8.2f %8.2f %8.2f\n", name.c_str(),
                          l->getMass() * 1e3, l->getVolume() * 1e6, am.x() * 1e3, am.y() * 1e3, am.z() * 1e3,
                          ai.x() * 1e4, ai.y() * 1e4, ai.z() * 1e4);
            os << buf;
            M += l->getMass();
            V += l->getVolume();
        }
        const double Vw = vbs_->getLiquidVolume();
        std::snprintf(buf, sizeof(buf),
                      "  SUMA   %9.1f %9.1f   (+ woda w VBS: %.1f ml = %.1f g)\n"
                      "  Wypadkowa pływalność (wypór − ciężar): %+.4f N  (bez wody w VBS: %+.4f N)\n"
                      "  Hydraulika: k_h = %.2f N·m/rad, wagi przegubów:",
                      M * 1e3, V * 1e6, Vw * 1e6, rho * Vw * 1e3,
                      (rho * V - M - rho * Vw) * g, (rho * V - M) * g, hyd_->StiffnessHydraulic());
        os << buf;
        for(double w : driver_->weights()) os << " " << w;
        os << stiffnessReport_ << frictionReport_;
        massReport_ = os.str();
    }

    // Tworzy hydraulikę i regulatory od zera (start symulacji).
    void FishSimManager::ResetControl()
    {
        const auto& h = cfg_.at("hydraulics");
        HydraulicsParams hp{h.at("A_eff"), h.at("r_eff"), h.at("C_h"), h.at("p_max"),
                            h.at("V0_chamber"), h.at("Q_max"), h.at("tau_pump")};
        hyd_ = std::make_unique<TailHydraulics>(hp);

        const auto& t = cfg_.at("tail");
        driver_ = std::make_unique<TailDriver>((int)motors_.size(), t.at("n_actuated").get<int>(),
                                               t.at("tendon_weight_last").get<double>(), JointStiffness());
        locked_ = t.at("locked").get<bool>();

        const auto& r = cfg_.at("rhythm");
        rhythm_ = std::make_unique<TailRhythm>(r.at("freq"), r.at("volume_amp"), r.at("volume_bias"),
                                               r.at("K_v"), hp.Q_max, r.at("ramp_time"));
        rhythmOn_ = r.at("enabled").get<bool>();

        const auto& d = cfg_.at("depth");
        const auto& v = cfg_.at("vbs");
        DepthParams dp{d.at("kp"), d.at("ki"), d.at("kd"), d.at("i_band"), d.at("lpf_cutoff_hz"), d.at("z_min"),
                       v.at("v_min"), v.at("v_max"), 0.5 * (v.at("v_min").get<double>() + v.at("v_max").get<double>())};
        depthCtrl_ = std::make_unique<DepthController>(dp);
        depthSchedule_ = d.at("schedule").get<std::vector<std::pair<double, double>>>();
        depthCtrl_->SetReference(depthSchedule_.front().second);
        depthOn_ = d.at("enabled").get<bool>();
        // regulator pracuje z częstotliwością czujnika ciśnienia (nowa próbka = nowa decyzja)
        depthEvery_ = std::max(1, (int)std::lround(cfg_.d("sim", "steps_per_second") / cfg_.d("sensors", "pressure_rate")));
        vbsRef_ = vbs_->getLiquidVolume();

        const auto& hd = cfg_.at("heading");
        headingCtrl_ = std::make_unique<HeadingController>(hd.at("kp"), hd.at("ki"), hd.at("bias_max"));
        headingOn_ = hd.at("enabled").get<bool>();
        yawRef_ = hd.at("yaw_ref_deg").get<double>() * M_PI / 180.0;

        rhoG_ = cfg_.d("materials", "rho_water") * 9.81;
    }

    // Współczynnik tarcia Stonefish (liniowy: F = ρ·c·Σ A·v_t) – patrz config "hydro".
    void FishSimManager::ApplySkinFriction()
    {
        const std::string mode = cfg_.s("hydro", "skin_friction");
        char buf[256];
        if(mode == "library")
        {
            sf::Vector3 Cd, Cf;
            links_[0]->getHydrodynamicCoefficients(Cd, Cf);
            std::snprintf(buf, sizeof(buf), "\n  Tarcie: współczynniki biblioteki (c = 0.1·Cd, głowa: %.3f %.3f %.3f m/s)", Cf.x(), Cf.y(), Cf.z());
            frictionReport_ = buf;
            return;
        }
        if(mode != "blasius")
            throw std::runtime_error("hydro.skin_friction musi być \"library\" albo \"blasius\"");

        // długość ryby: od nosa kadłuba do końca płetwy (ogon prosty)
        const auto& g = cfg_.at("geometry");
        const double nose = g.at("hull_semi_axes")[0].get<double>();
        const double finA = g.at("fin_semi_axes")[0].get<double>();
        const double tailEnd = g.at("tail_attach_x").get<double>() - g.at("n_segments").get<int>() * g.at("segment_length").get<double>()
                               - 2.0 * finA + g.at("segment_overlap").get<double>();
        const double Lfish = nose - tailEnd;
        const double U = cfg_.d("hydro", "U_ref");
        const double Re = U * Lfish / cfg_.d("hydro", "nu");
        const double CfBlasius = 1.328 / std::sqrt(Re);
        const double c = 0.5 * CfBlasius * U;
        for(auto* l : allLinks_)
        {
            sf::Vector3 Cd, Cf;
            l->getHydrodynamicCoefficients(Cd, Cf);               // opór ciśnieniowy zostaje z biblioteki
            l->SetHydrodynamicCoefficients(Cd, sf::Vector3(c, c, c));
        }
        std::snprintf(buf, sizeof(buf), "\n  Tarcie (Blasius): L = %.3f m, Re = %.0f, C_f = %.4f -> c = %.2e m/s (biblioteka: ~0.1)",
                      Lfish, Re, CfBlasius, c);
        frictionReport_ = buf;
    }

    // Sztywność przegubów: napędzane – z konfiguracji, pasywne – z rezonansu f_res:
    //   k_j = I_j·(2π·f_res)²,  I_j = Σ_{bryły za przegubem j} [I_aug,oś + M_aug·r²]
    // gdzie M_aug, I_aug to masa i bezwładność RAZEM z masą dołączoną wody, policzone przez
    // Stonefish, a r – odległość środka masy bryły od osi przegubu (ogon prosty, start).
    std::vector<double> FishSimManager::JointStiffness()
    {
        const auto& t = cfg_.at("tail");
        const int n = (int)motors_.size();
        if(t.contains("stiffness_override") && !t.at("stiffness_override").is_null())
            return t.at("stiffness_override").get<std::vector<double>>();

        const int nAct = t.at("n_actuated").get<int>();
        const double w = 2.0 * M_PI * t.at("passive_resonance_hz").get<double>();
        const double L = cfg_.d("geometry", "segment_length");
        const double x0 = cfg_.d("geometry", "tail_attach_x");
        const sf::Transform head = links_[0]->getOTransform();
        const sf::Vector3 axis = head.getBasis().getColumn(2);          // oś Z głowy = oś przegubów

        std::vector<double> k(n, t.at("stiffness_actuated").get<double>());
        std::ostringstream os;
        for(int j = nAct; j < n; ++j)
        {
            const sf::Vector3 pivot = head * sf::Vector3(x0 - j * L, 0, 0);
            double I = 0.0;
            for(size_t li = j + 1; li < links_.size(); ++li)              // Seg(j+1)..SegN, Fin
            {
                const sf::SolidEntity* l = links_[li];
                const sf::Transform cg = l->getCGTransform();
                sf::Vector3 r = cg.getOrigin() - pivot;
                r -= axis * r.dot(axis);                                   // składowa prostopadła do osi
                const sf::Vector3 Ip = l->getAugmentedInertia();          // w osiach głównych bryły
                const sf::Matrix3& R = cg.getBasis();
                double Iaxis = 0.0;
                for(int c = 0; c < 3; ++c)
                {
                    const double a = R.getColumn(c).dot(axis);
                    Iaxis += Ip[c] * a * a;
                }
                I += Iaxis + l->getAugmentedMass() * r.length2();
            }
            k[j] = I * w * w;
            char buf[160];
            std::snprintf(buf, sizeof(buf), "\n  Przegub pasywny %d: I = %.3f kg·cm² (z masą dołączoną) -> k = %.3f N·m/rad",
                          j + 1, I * 1e4, k[j]);
            os << buf;
        }
        stiffnessReport_ = os.str();
        return k;
    }

    // ================================================================== krok symulacji

    void FishSimManager::SimulationStepCompleted(sf::Scalar dt)
    {
        if(!parsedOk_ || robot_ == nullptr)
            return;
        const double t = getSimulationTime();

        // ---- 1) Pomiary: kąty i prędkości przegubów z enkoderów
        for(size_t i = 0; i < encoders_.size(); ++i)
        {
            theta_[i] = encoders_[i]->getLastValue(0);
            omega_[i] = encoders_[i]->getLastValue(1);
        }

        // ---- 2) Hydraulika ogona i momenty w przegubach
        L_ = driver_->TendonLength(theta_);
        u_ = rhythmOn_ ? rhythm_->Command(t, hyd_->Vp()) : 0.0;
        if(!rhythmOn_)
        {
            // CPG wyłączony: pompa trzyma objętość V_bias (ogon wraca do pozycji zadanej)
            u_ = std::clamp(cfg_.d("rhythm", "K_v") * (rhythm_->bias - hyd_->Vp()) / hyd_->params().Q_max, -1.0, 1.0);
        }
        F_ = hyd_->Step(u_, L_, dt);
        tau_ = driver_->JointTorques(F_, theta_, locked_);
        // Moment ustawiony teraz działa w NASTĘPNYM kroku fizyki (aktuatory są
        // aktualizowane na początku kroku) – to jawne sprzężenie, jak w MuJoCo.
        for(size_t i = 0; i < motors_.size(); ++i)
            motors_[i]->setIntensity(tau_[i]);
        double s = 0.0;
        for(double x : TailDriver::LinkTorques(tau_)) s += x;
        tauSum_ = s;

        // ---- 3) Kurs (IMU) -> skręt ogona
        if(headingOn_)
            rhythm_->bias = headingCtrl_->Update(imu_->getLastValue(2), yawRef_, dt);

        // ---- 4) Głębokość z czujnika ciśnienia -> VBS
        depthMeas_ = pressure_->getLastValue(0) / rhoG_;      // d = p / (ρ·g)
        if(depthOn_)
        {
            for(const auto& [ts, z] : depthSchedule_)
                if(t >= ts) depthCtrl_->SetReference(z);
            if(step_ % depthEvery_ == 0)
                vbsRef_ = depthCtrl_->Update(depthMeas_, dt * depthEvery_);
        }
        const auto& v = cfg_.at("vbs");
        vbsFlow_ = VbsFlowCommand(vbsRef_, vbs_->getLiquidVolume(), v.at("k_track"), v.at("q_max"));
        vbs_->setFlowRate(vbsFlow_);

        // ---- 5) Log
        if(!logPath_.empty() && step_ % logEvery_ == 0)
        {
            if(!log_.is_open())
            {
                log_.open(logPath_);
                if(!log_) throw std::runtime_error("Nie mogę zapisać logu: " + logPath_);
                WriteLogHeader();
            }
            WriteLogRow();
        }
        ++step_;

        if(!finished_ && t >= duration_ && onFinished_)
        {
            finished_ = true;
            if(log_.is_open()) log_.flush();
            onFinished_();
        }
    }

    // ================================================================== log CSV

    void FishSimManager::WriteLogHeader()
    {
        log_ << "# scenariusz: " << cfg_.s("sim", "scenario") << ", konfiguracja: " << cfg_.sourceFile << "\n";
        log_ << "# uklad NED: x do przodu, y w prawo, z w dol (z = glebokosc). Katy w rad, cisnienia w Pa, objetosci w m3.\n";
        log_ << "t,x,y,z,roll,pitch,yaw,vx,vy,vz,v_fwd,com_x,com_y,com_z,Px,Py,Lz,"
                "p_meas,depth_meas,depth_filt,depth_ref,imu_roll,imu_pitch,imu_yaw,imu_wz";
        for(size_t i = 1; i <= theta_.size(); ++i) log_ << ",theta" << i;
        for(size_t i = 1; i <= theta_.size(); ++i) log_ << ",omega" << i;
        for(size_t i = 1; i <= theta_.size(); ++i) log_ << ",tau" << i;
        log_ << ",tau_sum,L,u,Q,V_L,V_R,V_p,p_L,p_R,F,Q_valve,freq,V_bias,vbs_V,vbs_Vref,vbs_flow,fin_lift,fin_alpha_deg,fin_thrust,"
                "Fdrag_head,Fdrag_tail,Fdrag_fin,Fskin_all\n";
    }

    void FishSimManager::WriteLogRow()
    {
        const sf::Transform T = links_[0]->getOTransform();
        sf::Scalar yaw, pitch, roll;
        T.getBasis().getEulerYPR(yaw, pitch, roll);
        const sf::Vector3 vel = links_[0]->getLinearVelocity();
        const double vFwd = vel.dot(T.getBasis().getColumn(0));   // prędkość wzdłuż osi X głowy
        sf::Vector3 com, P;
        double Lz;
        ComputeMomentum(com, P, Lz);

        char buf[512];
        std::snprintf(buf, sizeof(buf), "%.4f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6e,%.6e,%.6e",
                      getSimulationTime(), T.getOrigin().x(), T.getOrigin().y(), T.getOrigin().z(), roll, pitch, yaw,
                      vel.x(), vel.y(), vel.z(), vFwd, com.x(), com.y(), com.z(), P.x(), P.y(), Lz);
        log_ << buf;
        std::snprintf(buf, sizeof(buf), ",%.2f,%.5f,%.5f,%.4f,%.6f,%.6f,%.6f,%.6f",
                      pressure_->getLastValue(0), depthMeas_, depthCtrl_->depthFiltered(), depthCtrl_->reference(),
                      imu_->getLastValue(0), imu_->getLastValue(1), imu_->getLastValue(2), imu_->getLastValue(5));
        log_ << buf;
        for(double x : theta_) { std::snprintf(buf, sizeof(buf), ",%.6f", x); log_ << buf; }
        for(double x : omega_) { std::snprintf(buf, sizeof(buf), ",%.6f", x); log_ << buf; }
        for(double x : tau_) { std::snprintf(buf, sizeof(buf), ",%.6e", x); log_ << buf; }
        // ciąg od siły nośnej = jej składowa wzdłuż osi X głowy
        const double finThrust = finLift_ ? finLift_->lastForceWorld().dot(T.getBasis().getColumn(0)) : 0.0;
        std::snprintf(buf, sizeof(buf), ",%.3e,%.6f,%.5f,%.6e,%.9e,%.9e,%.6e,%.2f,%.2f,%.6e,%.6e,%.4f,%.6e,%.6e,%.6e,%.6e,%.5f,%.2f,%.5f\n",
                      tauSum_, L_, u_, hyd_->Q(), hyd_->VL(), hyd_->VR(), hyd_->Vp(), hyd_->pL(L_), hyd_->pR(L_), F_,
                      hyd_->Qvalve(), rhythm_->freq(), rhythm_->bias, vbs_->getLiquidVolume(), vbsRef_, vbsFlow_,
                      finLift_ ? finLift_->lastLift() : 0.0, finLift_ ? finLift_->lastAlphaDeg() : 0.0, finThrust);
        std::string row(buf);
        row.pop_back();   // bez '\n' – dopisujemy jeszcze kolumny sił
        log_ << row;
        // Siły wody policzone przez Stonefish, rzut na oś X głowy (+ = do przodu):
        // opór "kwadratowy" (ciśnieniowy) głowy, segmentów ogona i płetwy oraz tarcie (wszystkie bryły).
        const sf::Vector3 ex = T.getBasis().getColumn(0);
        double dHead = 0, dTail = 0, dFin = 0, skin = 0;
        for(size_t i = 0; i < allLinks_.size(); ++i)
        {
            sf::Vector3 Fb, Tb, Fd, Td, Ff, Tf;
            allLinks_[i]->getHydrodynamicForces(Fb, Tb, Fd, Td, Ff, Tf);
            const double fx = Fd.dot(ex);
            // głowa razem z płetwą grzbietową; płetwa ogonowa = ostatnie ogniwo łańcucha ogona
            (i == 0 || i >= links_.size() ? dHead : (i + 1 == links_.size() ? dFin : dTail)) += fx;
            skin += Ff.dot(ex);
        }
        std::snprintf(buf, sizeof(buf), ",%.5f,%.5f,%.5f,%.5f\n", dHead, dTail, dFin, skin);
        log_ << buf;
    }

    void FishSimManager::ComputeMomentum(sf::Vector3& com, sf::Vector3& P, double& Lz) const
    {
        // Środek masy i pęd: suma po bryłach. Moment pędu względem osi Z przechodzącej
        // przez środek masy: Σ [m·(r − r_c) × v + R·I·Rᵀ·ω]_z, I – główne momenty bezwładności
        // w układzie CG bryły (R = orientacja tego układu).
        double M = 0.0;
        com.setZero();
        P.setZero();
        for(auto* l : allLinks_)
        {
            M += l->getMass();
            com += l->getMass() * l->getCGTransform().getOrigin();
            P += l->getMass() * l->getLinearVelocity();
        }
        com /= M;
        Lz = 0.0;
        for(auto* l : allLinks_)
        {
            const sf::Transform cg = l->getCGTransform();
            const sf::Vector3 r = cg.getOrigin() - com;
            const sf::Vector3 I = l->getInertia();
            const sf::Matrix3 R = cg.getBasis();
            const sf::Matrix3 Iw = R * sf::Matrix3(I.x(), 0, 0, 0, I.y(), 0, 0, 0, I.z()) * R.transpose();
            Lz += (l->getMass() * r.cross(l->getLinearVelocity())).z() + (Iw * l->getAngularVelocity()).z();
        }
    }

    // ================================================================== sterowanie z klawiatury

    void FishSimManager::ToggleRhythm() { rhythmOn_ = !rhythmOn_; }

    void FishSimManager::ChangeFreq(double df)
    {
        const double f = std::clamp(rhythm_->freq() + df, 0.25, 3.5);
        rhythm_->SetFreq(f, getSimulationTime());
    }

    void FishSimManager::ChangeBias(double dV)
    {
        headingOn_ = false;   // ręczny skręt wyłącza regulator kursu
        rhythm_->bias = std::clamp(rhythm_->bias + dV, -4e-6, 4e-6);
    }

    void FishSimManager::ChangeDepthRef(double dz)
    {
        depthOn_ = true;
        depthSchedule_.clear();
        depthCtrl_->SetReference(depthCtrl_->reference() + dz);
    }

    FishStatus FishSimManager::Status() const
    {
        FishStatus s;
        if(!parsedOk_ || links_.empty()) return s;
        const sf::Transform T = links_[0]->getOTransform();
        sf::Scalar yaw, pitch, roll;
        T.getBasis().getEulerYPR(yaw, pitch, roll);
        s.t = getSimulationTime();
        s.speed = links_[0]->getLinearVelocity().dot(T.getBasis().getColumn(0));
        s.depth = T.getOrigin().z();
        s.depthMeas = depthMeas_;
        s.depthRef = depthCtrl_->reference();
        s.freq = rhythm_->freq();
        s.biasMl = rhythm_->bias * 1e6;
        s.pL = hyd_->pL(L_);
        s.pR = hyd_->pR(L_);
        s.vbsMl = vbs_->getLiquidVolume() * 1e6;
        s.yawDeg = yaw * 180.0 / M_PI;
        s.rhythmOn = rhythmOn_;
        s.depthOn = depthOn_;
        s.headingOn = headingOn_;
        return s;
    }
}
