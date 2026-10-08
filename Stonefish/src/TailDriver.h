// TailDriver – converts the hydraulic force into torques in the tail joints.
//
// The hydraulics give a single torque F on the "tendon" (a virtual cable) of length
// L = Σ w_i·θ_i. By the principle of virtual work, the torque in joint i is τ_i = w_i·F
// (joints closer to the root have larger chambers -> larger weights).
// Plus the silicone elasticity, which Stonefish does not have in its joints: −k_i·θ_i.
//
//   τ_i = w_i·F − k_i·θ_i
//
// Where the torques go: the "motor" actuator calls FeatherstoneEntity::DriveJoint,
// i.e. btMultiBody::addJointTorque – the generalized joint force. In Featherstone's
// algorithm such a torque acts on the CHILD (+τ·axis) and on the PARENT (−τ·axis) simultaneously,
// so the net drive torque on the whole robot = 0 (internal actuation).
// LinkTorques() computes this distribution explicitly – for the test and the log.
//
// The class does not depend on Stonefish (it can be tested without the simulator).
#pragma once

#include <vector>

namespace fish
{
    class TailDriver
    {
    public:
        // nJoints – number of tail joints, nActuated – how many of the first ones the hydraulics drive,
        // weightLast – weight of the last driven joint (first = 1, linear),
        // stiffness – k_i for each joint [N·m/rad].
        TailDriver(int nJoints, int nActuated, double weightLast, const std::vector<double>& stiffness);

        // L = Σ w_i·θ_i [rad]
        double TendonLength(const std::vector<double>& theta) const;

        // τ_i = w_i·F − k_i·θ_i. When locked = true – zeros (tail not driven).
        std::vector<double> JointTorques(double F, const std::vector<double>& theta, bool locked = false) const;

        // Torques (component along the joint axes, all axes parallel = Z) acting
        // on successive bodies: [head, seg1, ..., segN]. Body k gets +τ_k from its own
        // joint (it is the child) and −τ_{k+1} from the next joint (it is the parent).
        // The sum is always = 0 – this is checked in the tests.
        static std::vector<double> LinkTorques(const std::vector<double>& jointTorques);

        const std::vector<double>& weights() const { return w_; }
        const std::vector<double>& stiffness() const { return k_; }
        int nJoints() const { return (int)w_.size(); }

    private:
        std::vector<double> w_;
        std::vector<double> k_;
    };
}
