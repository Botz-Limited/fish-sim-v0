#include "TailDriver.h"

#include <stdexcept>

namespace fish
{
    TailDriver::TailDriver(int nJoints, int nActuated, double weightLast, const std::vector<double>& stiffness)
        : w_(nJoints, 0.0), k_(stiffness)
    {
        if(nActuated < 1 || nActuated > nJoints)
            throw std::runtime_error("tail.n_actuated musi być w zakresie 1..liczba przegubów");
        if((int)k_.size() != nJoints)
            throw std::runtime_error("tail.stiffness musi mieć tyle elementów, ile jest przegubów ogona");
        // Wagi malejące liniowo od 1 (nasada) do weightLast (ostatni napędzany),
        // przeguby pasywne mają wagę 0 – hydraulika ich nie "widzi".
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
        std::vector<double> link(n + 1, 0.0);     // [głowa, seg1..segN]
        for(size_t i = 0; i < n; ++i)
        {
            link[i] -= jointTorques[i];           // rodzic przegubu i (głowa dla i = 0)
            link[i + 1] += jointTorques[i];       // dziecko przegubu i
        }
        return link;
    }
}
