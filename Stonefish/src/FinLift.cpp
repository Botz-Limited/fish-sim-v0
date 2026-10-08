#include "FinLift.h"

#include <Stonefish/core/SimulationApp.h>
#include <Stonefish/core/SimulationManager.h>
#include <Stonefish/entities/SolidEntity.h>
#include <Stonefish/entities/forcefields/Ocean.h>

#include <cmath>

namespace fish
{
    void FinLiftForce(double ux, double uy, double rho, double area, double clAlpha, double& Lx, double& Ly)
    {
        Lx = Ly = 0.0;
        const double u2 = ux * ux + uy * uy;
        if(u2 < 1e-12)
            return;
        // Płytka jest symetryczna: przepływ od tyłu traktujemy jak od przodu -> α ∈ [0, π/2].
        const double alpha = std::atan2(std::fabs(uy), std::fabs(ux));
        const double CL = 0.5 * clAlpha * std::sin(2.0 * alpha);
        const double L = 0.5 * rho * area * CL * u2;
        // kierunek prostopadły do u; wybieramy ten, którego składowa Y jest PRZECIWNA do uy
        // (siła ciśnienia hamuje ruch płetwy w kierunku jej normalnej)
        const double n = std::sqrt(u2);
        double px = -uy / n, py = ux / n;
        if(py * uy > 0.0) { px = -px; py = -py; }
        Lx = L * px;
        Ly = L * py;
    }

    FinLift::FinLift(const std::string& name, double area, double clAlpha)
        : sf::LinkActuator(name), area_(area), clAlpha_(clAlpha), Fw_(0, 0, 0)
    {
    }

    void FinLift::Update(sf::Scalar dt)
    {
        sf::Actuator::Update(dt);
        lift_ = 0.0;
        Fw_.setZero();
        sf::Ocean* ocn = sf::SimulationApp::getApp()->getSimulationManager()->getOcean();
        if(attach == nullptr || ocn == nullptr)
            return;

        // Układ płetwy (actuator frame) w świecie i punkt przyłożenia względem środka masy ogniwa.
        const sf::Transform T = attach->getOTransform() * o2a;
        if(!ocn->IsInsideFluid(T.getOrigin()))
            return;
        const sf::Vector3 rel = T.getOrigin() - attach->getCGTransform().getOrigin();
        const sf::Vector3 v = attach->getLinearVelocityInLocalPoint(rel) - ocn->GetFluidVelocity(T.getOrigin());
        const sf::Vector3 u = T.getBasis().transpose() * v;     // w układzie płetwy

        double Lx, Ly;
        const double rho = ocn->getLiquid().density;
        FinLiftForce(u.x(), u.y(), rho, area_, clAlpha_, Lx, Ly);
        lift_ = std::sqrt(Lx * Lx + Ly * Ly);
        alphaDeg_ = std::atan2(std::fabs(u.y()), std::fabs(u.x())) * 180.0 / M_PI;

        Fw_ = T.getBasis() * sf::Vector3(Lx, Ly, 0.0);
        attach->ApplyCentralForce(Fw_);
        attach->ApplyTorque(rel.cross(Fw_));
    }
}
