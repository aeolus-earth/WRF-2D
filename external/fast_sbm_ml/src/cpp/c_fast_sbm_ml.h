extern "C" {
     void c_fast_sbm_ml_(
        const double* c_w, const double* c_u, const double* c_v, double* c_th_old,
        double* c_chem_new, const int* c_n_chem,
        const int* c_itimestep, const double* c_dt, const double* c_dx, const double* c_dy,
        const double* c_dz8w, const double* c_rho_phy, const double* c_p_phy, const double* c_pi_phy, double* c_th_phy,
        const double* c_xland, const int* c_domain_id, const int* c_ivgtyp, const double* c_xlat, const double* c_xlong,
        double* c_qv, double* c_qc, double* c_qr, double* c_qi, double* c_qs, double* c_qg, double* c_qv_old,
        double* c_qnc, double* c_qnr, double* c_qni, double* c_qns, double* c_qng, double* c_qna,
        const int* c_ids, const int* c_ide, const int* c_jds, const int* c_jde, const int* c_kds, const int* c_kde,
        const int* c_ims, const int* c_ime, const int* c_jms, const int* c_jme, const int* c_kms, const int* c_kme,
        const int* c_its, const int* c_ite, const int* c_jts, const int* c_jte, const int* c_kts, const int* c_kte,
        const bool* c_diagflag,
        double* c_sbmradar, const int* c_num_sbmradar,
        const int* c_sbm_diagnostics,
        double* c_rainnc, double* c_rainncv, double* c_snownc, double* c_snowncv,
        double* c_graupelnc, double* c_graupelncv, double* c_sr
    );
}