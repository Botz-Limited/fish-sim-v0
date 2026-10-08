// TailDriver – zamiana siły hydrauliki na momenty w przegubach ogona.
//
// Hydraulika daje jeden moment F na "tendonie" (wirtualnym cięgnie) o długości
// L = Σ w_i·θ_i. Z zasady prac przygotowanych moment w przegubie i to τ_i = w_i·F
// (przeguby bliżej nasady mają większe komory -> większe wagi).
// Do tego sprężystość silikonu, której Stonefish nie ma w przegubach: −k_i·θ_i.
//
//   τ_i = w_i·F − k_i·θ_i
//
// Gdzie trafiają momenty: aktuator "motor" wywołuje FeatherstoneEntity::DriveJoint,
// czyli btMultiBody::addJointTorque – uogólnioną siłę przegubu. W algorytmie
// Featherstone'a taki moment działa na DZIECKO (+τ·oś) i na RODZICA (−τ·oś) jednocześnie,
// więc wypadkowy moment od napędu na całego robota = 0 (napęd wewnętrzny).
// LinkTorques() liczy ten rozkład jawnie – do testu i do logu.
//
// Klasa nie zależy od Stonefish (da się ją testować bez symulatora).
#pragma once

#include <vector>

namespace fish
{
    class TailDriver
    {
    public:
        // nJoints – liczba przegubów ogona, nActuated – ile pierwszych napędza hydraulika,
        // weightLast – waga ostatniego napędzanego (pierwszy = 1, liniowo),
        // stiffness – k_i dla każdego przegubu [N·m/rad].
        TailDriver(int nJoints, int nActuated, double weightLast, const std::vector<double>& stiffness);

        // L = Σ w_i·θ_i [rad]
        double TendonLength(const std::vector<double>& theta) const;

        // τ_i = w_i·F − k_i·θ_i. Gdy locked = true – zera (ogon bez napędu).
        std::vector<double> JointTorques(double F, const std::vector<double>& theta, bool locked = false) const;

        // Momenty (składowa wzdłuż osi przegubów, wszystkie osie równoległe = Z) działające
        // na kolejne bryły: [głowa, seg1, ..., segN]. Bryła k dostaje +τ_k od swojego
        // przegubu (jest dzieckiem) i −τ_{k+1} od przegubu następnego (jest rodzicem).
        // Suma zawsze = 0 – to jest sprawdzane w testach.
        static std::vector<double> LinkTorques(const std::vector<double>& jointTorques);

        const std::vector<double>& weights() const { return w_; }
        const std::vector<double>& stiffness() const { return k_; }
        int nJoints() const { return (int)w_.size(); }

    private:
        std::vector<double> w_;
        std::vector<double> k_;
    };
}
