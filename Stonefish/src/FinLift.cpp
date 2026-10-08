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
        // The plate is symmetric: flow from behind is treated like flow from the front -> α ∈ [0, π/2].
        const double alpha = std::atan2(std::fabs(uy), std::fabs(ux));
        const double CL = 0.5 * clAlpha * std::sin(2.0 * alpha);
        const double L = 0.5 * rho * area * CL * u2;
        // direction perpendicular to u; we pick the one whose Y component is OPPOSITE to uy
        // (the pressure force resists the fin motion along its normal)
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

        // Fin frame (actuator frame) in the world and the point of application relative to the link's center of mass.
        const sf::Transform T = attach->getOTransform() * o2a;
        if(!ocn->IsInsideFluid(T.getOrigin()))
            return;
        const sf::Vector3 rel = T.getOrigin() - attach->getCGTransform().getOrigin();
        const sf::Vector3 v = attach->getLinearVelocityInLocalPoint(rel) - ocn->GetFluidVelocity(T.getOrigin());
        const sf::Vector3 u = T.getBasis().transpose() * v;     // in the fin frame

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
