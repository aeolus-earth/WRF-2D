#if( BUILD_SBM_FAST != 1)
      MODULE module_mp_fast_sbm
      CONTAINS
      SUBROUTINE SBM_fast
         REAL :: dummy
         dummy = 1
      END SUBROUTINE SBM_fast
      END MODULE module_mp_fast_sbm

! Stub modules
module module_mp_SBM_BreakUp
end module module_mp_SBM_BreakUp

module module_mp_SBM_Collision
end module module_mp_SBM_Collision

module module_mp_SBM_Auxiliary
end module module_mp_SBM_Auxiliary

module module_mp_SBM_Nucleation
end module module_mp_SBM_Nucleation

#else

module module_mp_SBM_BreakUp
end module module_mp_SBM_BreakUp

module module_mp_SBM_Collision
end module module_mp_SBM_Collision

module module_mp_SBM_Auxiliary
end module module_mp_SBM_Auxiliary

module module_mp_SBM_Nucleation
end module module_mp_SBM_Nucleation

MODULE module_mp_fast_sbm

  USE, INTRINSIC :: iso_c_binding
  IMPLICIT NONE
  PRIVATE
  PUBLIC FAST_SBM, FAST_HUCMINIT

  !---------------------------------------------------------------------
  ! 1) Interface to the minimal C++ no-op function
  !---------------------------------------------------------------------
  INTERFACE
    subroutine c_fast_sbm_ml(w, u, v, th_old, &
                               chem_new, n_chem, &
                               itimestep, dt, dx, dy, &
                               dz8w, rho_phy, p_phy, pi_phy, th_phy, &
                               xland, domain_id, ivgtyp, xlat, xlong, &
                               qv, qc, qr, qi, qs, qg, qv_old, &
                               qnc, qnr, qni, qns, qng, qna, &
                               ids, ide, jds, jde, kds, kde, &
                               ims, ime, jms, jme, kms, kme, &
                               its, ite, jts, jte, kts, kte, &
                               diagflag, &
                               sbmradar, num_sbmradar, &
                               sbm_diagnostics, &
                               rainnc, rainncv, snownc, snowncv, &
                               graupelnc, graupelncv, sr) bind(C, name="c_fast_sbm_ml_")
            import :: c_float, c_int, c_bool
            real(c_float), intent(in), dimension(*) :: w, u, v
            real(c_float), intent(inout), dimension(*) :: th_old
            real(c_float), intent(inout), dimension(*) :: chem_new
            integer(c_int), intent(in) :: n_chem
            integer(c_int), intent(in) :: itimestep
            real(c_float), intent(in) :: dt, dx, dy
            real(c_float), intent(in), dimension(*) :: dz8w, rho_phy, p_phy, pi_phy
            real(c_float), intent(inout), dimension(*) :: th_phy
            real(c_float), intent(in), dimension(*) :: xland
            integer(c_int), intent(in) :: domain_id
            integer(c_int), intent(in), dimension(*) :: ivgtyp
            real(c_float), intent(in), dimension(*) :: xlat, xlong
            real(c_float), intent(inout), dimension(*) :: qv, qc, qr, qi, qs, qg, qv_old
            real(c_float), intent(inout), dimension(*) :: qnc, qnr, qni, qns, qng, qna
            integer(c_int), intent(in) :: ids, ide, jds, jde, kds, kde
            integer(c_int), intent(in) :: ims, ime, jms, jme, kms, kme
            integer(c_int), intent(in) :: its, ite, jts, jte, kts, kte
            logical(c_bool), intent(in) :: diagflag
            real(c_float), intent(inout), dimension(*) :: sbmradar
            integer(c_int), intent(in) :: num_sbmradar
            integer(c_int), intent(in) :: sbm_diagnostics
            real(c_float), intent(inout), dimension(*) :: rainnc, rainncv, snownc, snowncv
            real(c_float), intent(inout), dimension(*) :: graupelnc, graupelncv, sr
        end subroutine c_fast_sbm_ml


  END INTERFACE

CONTAINS

  !----------------------------------------------------------------------
  ! 2) The no-op microphysics subroutine with ALL arguments.
  !    We embed flatten/unflatten logic for chem_new so that we can
  !    call the C++ function c_fast_sbm_ml_.
  !----------------------------------------------------------------------
  SUBROUTINE FAST_SBM( w,u,v,th_old,                                &
      &                 chem_new,n_chem,                            &
      &                 itimestep,dt,dx,dy,                         &
      &                 dz8w,rho_phy,p_phy,pi_phy,th_phy,           &
      &                 xland,domain_id,ivgtyp,xlat,xlong,          &
      &                 qv,qc,qr,qi,qs,qg,qv_old,                   &
      &                 qnc,qnr,qni,qns,qng,qna,                    &
      &                 ids,ide,jds,jde,kds,kde,                    &
      &                 ims,ime,jms,jme,kms,kme,                    &
      &                 its,ite,jts,jte,kts,kte,                    &
      &                 diagflag,                                   &
      &                 sbmradar,num_sbmradar,                      &
      &                 sbm_diagnostics,                            &
      &                 rainnc, rainncv, snownc, snowncv,           &
      &                 graupelnc, graupelncv, sr )

    IMPLICIT NONE

    ! ------------------------------
    ! (A) SCALARS
    ! ------------------------------
    INTEGER, INTENT(IN) :: itimestep, n_chem, num_sbmradar, domain_id
    INTEGER, INTENT(IN) :: sbm_diagnostics
    REAL,  INTENT(IN)   :: dt, dx, dy
    LOGICAL, OPTIONAL, INTENT(IN) :: diagflag

    ! ------------------------------
    ! (B) 3D FIELDS
    ! ------------------------------
    INTEGER, INTENT(IN) :: ids, ide, jds, jde, kds, kde
    INTEGER, INTENT(IN) :: ims, ime, jms, jme, kms, kme
    INTEGER, INTENT(IN) :: its, ite, jts, jte, kts, kte

    REAL, INTENT(IN)  :: w   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: u   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: v   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: dz8w(ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: rho_phy(ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: p_phy  (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: pi_phy (ims:ime, kms:kme, jms:jme)

    REAL, INTENT(INOUT) :: th_old (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: th_phy (ims:ime, kms:kme, jms:jme)

    REAL, INTENT(INOUT) :: qv     (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qc     (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qr     (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qi     (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qs     (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qg     (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qv_old (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qnc    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qnr    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qni    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qns    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qng    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: qna    (ims:ime, kms:kme, jms:jme)

    ! ------------------------------
    ! (C) 2D FIELDS
    ! ------------------------------
    REAL, INTENT(IN)  :: xland (ims:ime, jms:jme)
    INTEGER, INTENT(IN):: ivgtyp(ims:ime, jms:jme)
    REAL, INTENT(IN)   :: xlat  (ims:ime, jms:jme)
    REAL, INTENT(IN)   :: xlong (ims:ime, jms:jme)

    ! ------------------------------
    ! (D) 4D for chem
    ! ------------------------------
    REAL, INTENT(INOUT) :: chem_new(ims:ime, kms:kme, jms:jme, n_chem)

    ! ------------------------------
    ! (E) radar, accumulators, etc.
    ! ------------------------------
    REAL, INTENT(INOUT) :: sbmradar (ims:ime, kms:kme, jms:jme, num_sbmradar)
    REAL, INTENT(INOUT), OPTIONAL :: rainnc   (ims:ime, jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: rainncv  (ims:ime, jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: snownc   (ims:ime, jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: snowncv  (ims:ime, jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: graupelnc (ims:ime, jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: graupelncv(ims:ime, jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: sr(ims:ime, jms:jme)

    ! C-compatible scalar values
    INTEGER(c_int) :: c_itimestep, c_n_chem, c_num_sbmradar, c_domain_id
    INTEGER(c_int) :: c_sbm_diagnostics
    LOGICAL(c_bool) :: c_diagflag
    
    INTEGER(c_int) :: c_ids, c_ide, c_jds, c_jde, c_kds, c_kde
    INTEGER(c_int) :: c_ims, c_ime, c_jms, c_jme, c_kms, c_kme
    INTEGER(c_int) :: c_its, c_ite, c_jts, c_jte, c_kts, c_kte

    ! ------------------------------
    ! 1) Convert scalar values to C types
    ! ------------------------------
    c_itimestep = INT(itimestep, c_int)
    c_n_chem = INT(n_chem, c_int)
    c_num_sbmradar = INT(num_sbmradar, c_int)
    c_domain_id = INT(domain_id, c_int)
    c_sbm_diagnostics = INT(sbm_diagnostics, c_int)

    c_ids = INT(ids, c_int)
    c_ide = INT(ide, c_int)
    c_jds = INT(jds, c_int)
    c_jde = INT(jde, c_int)
    c_kds = INT(kds, c_int)
    c_kde = INT(kde, c_int)
    
    c_ims = INT(ims, c_int)
    c_ime = INT(ime, c_int)
    c_jms = INT(jms, c_int)
    c_jme = INT(jme, c_int)
    c_kms = INT(kms, c_int)
    c_kme = INT(kme, c_int)
    
    c_its = INT(its, c_int)
    c_ite = INT(ite, c_int)
    c_jts = INT(jts, c_int)
    c_jte = INT(jte, c_int)
    c_kts = INT(kts, c_int)
    c_kte = INT(kte, c_int)
    
    IF (PRESENT(diagflag)) THEN
      c_diagflag = LOGICAL(diagflag, c_bool)
    ELSE
      c_diagflag = .FALSE._c_bool
    END IF

    ! ------------------------------
    ! 6) Call the C++ function
    ! ------------------------------
    CALL c_fast_sbm_ml( w, u, v, th_old, &
      & chem_new, c_n_chem, &
      & c_itimestep, dt, dx, dy, &
      & dz8w, rho_phy, p_phy, pi_phy, th_phy, &
      & xland, c_domain_id, ivgtyp, xlat, xlong, &
      & qv, qc, qr, qi, qs, qg, qv_old, &
      & qnc, qnr, qni, qns, qng, qna, &
      & c_ids, c_ide, c_jds, c_jde, c_kds, c_kde, &
      & c_ims, c_ime, c_jms, c_jme, c_kms, c_kme, &
      & c_its, c_ite, c_jts, c_jte, c_kts, c_kte, &
      & c_diagflag, &
      & sbmradar, c_num_sbmradar, &
      & c_sbm_diagnostics, &
      & rainnc, rainncv, snownc, snowncv, &
      & graupelnc, graupelncv, sr )

    RETURN
  END SUBROUTINE FAST_SBM

  !----------------------------------------------------------------------
  ! 3) FAST_HUCMINIT => remains no-op
  !----------------------------------------------------------------------
  SUBROUTINE FAST_HUCMINIT(dt)
    IMPLICIT NONE
    REAL, INTENT(IN) :: dt
    RETURN
  END SUBROUTINE FAST_HUCMINIT

END MODULE module_mp_fast_sbm



#endif