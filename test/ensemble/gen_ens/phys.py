import numpy as np

Rv = 461.
Rd = 287.
eps = Rd / Rv
cpd = 1007.
cpv = 1952.
cw = 4218.
Lv = 2.5e6
P00 = 1e5
T00 = 300.
g = 9.81

func_T = lambda P, theta, Qv: theta * (P / P00) ** (func_R(Qv) / func_cp(Qv))

func_cp      = lambda       Qv : cpd / (1 - Qv / (cpd/(cpv-cpd) + Qv))
func_R       = lambda       Qv : Rd  / (1 - Qv / ( Rd/( Rv- Rd) + Qv))
func_esl     = lambda    T     : 2.53e11 * np.exp(-5.42e3 / T)
func_e       = lambda P,    Qv : Qv * P * Rv / (Rd + (Rv-Rd)*Qv)
func_Qv      = lambda P, e     : eps * e / (P - (1 - eps)*e)
func_theta   = lambda P, T, Qv : T * (P00 / P) ** (func_R(Qv) / func_cp(Qv))  
func_RHl     = lambda P, T, Qv : func_e(P, Qv) / func_esl(T)
func_theta_e = lambda P, T, Qv : T * (P00 / (P - func_e(P, Qv))) ** (Rd / (cpd + Qv*cw)) \
                                   * func_RHl(P, T, Qv) ** (- Qv*Rv / (cpd + Qv*cw))   \
                                   * np.exp( Lv * Qv / (T * (cpd + Qv*cw)) )

h_ml = 500
dtheta_l0 = 1.25