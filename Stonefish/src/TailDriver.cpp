#include "TailDriver.h"

#include <stdexcept>

namespace fish
{
    TailDriver::TailDriver(int nJoints, int nActuated, double weightLast, const std::vector<double>& stiffness)
        : w_(nJoints, 0.0), k_(stiffness)
    {
        if(nActuated < 1 || nActuated > nJoints)
            throw std::runtime_error("tail.n_actuated must be in the range 1..number of joints");
        if((int)k_.size() != nJoints)
            throw std::runtime_error("tail.stiffness must have as many elements as there are tail joints");
        // Weights decreasing linearly from 1 (root) to weightLast (last driven joint),
        // passive joints have weight 0 – the hydraulics do not "see" them.
        for(int i = 0; i < nActuated; ++i)
            w_[i] = nActuated == 1 ? 1.0 : 1.0 + (weightLast - 1.0) * i / (nActuated - 1);
    }

    double TailDriver::TendonLength(const std::vector<double>& theta) const
    {
        double L = 0.0;
        for(size_t i = 0; i < w_.size(); ++i)
            L += w_[i] * theta[i];
        return L;
    }

    std::vector<double> TailDriver::JointTorques(double F, const std::vector<double>& theta, bool locked) const
    {
        std::vector<double> tau(w_.size(), 0.0);
        if(locked)
            return tau;
        for(size_t i = 0; i < w_.size(); ++i)
            tau[i] = w_[i] * F - k_[i] * theta[i];
        return tau;
    }

    std::vector<double> TailDriver::LinkTorques(const std::vector<double>& jointTorques)
    {
        const size_t n = jointTorques.size();
        std::vector<double> link(n + 1, 0.0);     // [head, seg1..segN]
        for(size_t i = 0; i < n; ++i)
        {
            link[i] -= jointTorques[i];           // parent of joint i (head for i = 0)
            link[i + 1] += jointTorques[i];       // child of joint i
        }
        return link;
    }
}
