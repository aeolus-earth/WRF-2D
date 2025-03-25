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
    SUBROUTINE c_fast_sbm_ml ( w,u,v,th_old,                        &
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
      &                 graupelnc, graupelncv, sr ) BIND(C, name="c_fast_sbm_ml_")
      USE, INTRINSIC :: iso_c_binding
      IMPLICIT NONE

      ! ------------------------------
      ! (A) SCALARS
      ! ------------------------------
      INTEGER(c_int), INTENT(IN) :: itimestep, n_chem, num_sbmradar, domain_id
      INTEGER(c_int), INTENT(IN) :: sbm_diagnostics
      REAL(c_double),  INTENT(IN)   :: dt, dx, dy
      LOGICAL(C_BOOL), OPTIONAL, INTENT(IN) :: diagflag

      ! ------------------------------
      ! (B) 3D FIELDS
      ! ------------------------------
      INTEGER(c_int), INTENT(IN) :: ids, ide, jds, jde, kds, kde
      INTEGER(c_int), INTENT(IN) :: ims, ime, jms, jme, kms, kme
      INTEGER(c_int), INTENT(IN) :: its, ite, jts, jte, kts, kte

      REAL(c_double), INTENT(IN)  :: w   (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(IN)  :: u   (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(IN)  :: v   (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(IN)  :: dz8w(ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(IN)  :: rho_phy(ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(IN)  :: p_phy  (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(IN)  :: pi_phy (ims:ime, kms:kme, jms:jme)

      REAL(c_double), INTENT(INOUT) :: th_old (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: th_phy (ims:ime, kms:kme, jms:jme)

      REAL(c_double), INTENT(INOUT) :: qv     (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qc     (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qr     (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qi     (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qs     (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qg     (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qv_old (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qnc    (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qnr    (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qni    (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qns    (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qng    (ims:ime, kms:kme, jms:jme)
      REAL(c_double), INTENT(INOUT) :: qna    (ims:ime, kms:kme, jms:jme)

      ! ------------------------------
      ! (C) 2D FIELDS
      ! ------------------------------
      REAL(c_double), INTENT(IN)  :: xland (ims:ime, jms:jme)
      INTEGER(c_int), INTENT(IN):: ivgtyp(ims:ime, jms:jme)
      REAL(c_double), INTENT(IN)   :: xlat  (ims:ime, jms:jme)
      REAL(c_double), INTENT(IN)   :: xlong (ims:ime, jms:jme)

      ! ------------------------------
      ! (D) 4D for chem
      ! ------------------------------
      REAL(c_double), INTENT(INOUT) :: chem_new(ims:ime, kms:kme, jms:jme, n_chem)

      ! ------------------------------
      ! (E) radar, accumulators, etc.
      ! ------------------------------
      REAL(c_double), INTENT(INOUT) :: sbmradar (ims:ime, kms:kme, jms:jme, num_sbmradar)
      REAL(c_double), INTENT(INOUT), OPTIONAL :: rainnc   (ims:ime, jms:jme)
      REAL(c_double), INTENT(INOUT), OPTIONAL :: rainncv  (ims:ime, jms:jme)
      REAL(c_double), INTENT(INOUT), OPTIONAL :: snownc   (ims:ime, jms:jme)
      REAL(c_double), INTENT(INOUT), OPTIONAL :: snowncv  (ims:ime, jms:jme)
      REAL(c_double), INTENT(INOUT), OPTIONAL :: graupelnc  (ims:ime, jms:jme)
      REAL(c_double), INTENT(INOUT), OPTIONAL :: graupelncv (ims:ime, jms:jme)
      REAL(c_double), INTENT(INOUT), OPTIONAL :: sr  (ims:ime, jms:jme)
    END SUBROUTINE c_fast_sbm_ml
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



    ! ------------------------------
    ! Temporary variables for C binding
    ! ------------------------------
    REAL(c_double), ALLOCATABLE :: c_w(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_u(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_v(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_th_old(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_dz8w(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_rho_phy(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_p_phy(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_pi_phy(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_th_phy(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qv(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qc(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qr(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qi(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qs(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qg(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qv_old(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qnc(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qnr(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qni(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qns(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qng(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_qna(:,:,:)
    REAL(c_double), ALLOCATABLE :: c_xland(:,:)
    INTEGER(c_int), ALLOCATABLE :: c_ivgtyp(:,:)
    REAL(c_double), ALLOCATABLE :: c_xlat(:,:)
    REAL(c_double), ALLOCATABLE :: c_xlong(:,:)
    REAL(c_double), ALLOCATABLE :: c_chem_new(:,:,:,:)
    REAL(c_double), ALLOCATABLE :: c_sbmradar(:,:,:,:)
    REAL(c_double), ALLOCATABLE :: c_rainnc(:,:)
    REAL(c_double), ALLOCATABLE :: c_rainncv(:,:)
    REAL(c_double), ALLOCATABLE :: c_snownc(:,:)
    REAL(c_double), ALLOCATABLE :: c_snowncv(:,:)
    REAL(c_double), ALLOCATABLE :: c_graupelnc(:,:)
    REAL(c_double), ALLOCATABLE :: c_graupelncv(:,:)
    REAL(c_double), ALLOCATABLE :: c_sr(:,:)
    
    ! C-compatible scalar values
    INTEGER(c_int) :: c_itimestep, c_n_chem, c_num_sbmradar, c_domain_id
    INTEGER(c_int) :: c_sbm_diagnostics
    REAL(c_double) :: c_dt, c_dx, c_dy
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
    c_dt = REAL(dt, c_double)
    c_dx = REAL(dx, c_double)
    c_dy = REAL(dy, c_double)
    
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
    ! 2) Allocate and copy 3D arrays
    ! ------------------------------
    ALLOCATE(c_w(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_u(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_v(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_th_old(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_dz8w(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_rho_phy(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_p_phy(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_pi_phy(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_th_phy(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qv(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qc(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qr(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qi(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qs(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qg(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qv_old(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qnc(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qnr(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qni(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qns(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qng(ims:ime, kms:kme, jms:jme))
    ALLOCATE(c_qna(ims:ime, kms:kme, jms:jme))
    
    ! Copy 3D arrays to C-compatible arrays
    c_w = REAL(w, c_double)
    c_u = REAL(u, c_double)
    c_v = REAL(v, c_double)
    c_th_old = REAL(th_old, c_double)
    c_dz8w = REAL(dz8w, c_double)
    c_rho_phy = REAL(rho_phy, c_double)
    c_p_phy = REAL(p_phy, c_double)
    c_pi_phy = REAL(pi_phy, c_double)
    c_th_phy = REAL(th_phy, c_double)
    c_qv = REAL(qv, c_double)
    c_qc = REAL(qc, c_double)
    c_qr = REAL(qr, c_double)
    c_qi = REAL(qi, c_double)
    c_qs = REAL(qs, c_double)
    c_qg = REAL(qg, c_double)
    c_qv_old = REAL(qv_old, c_double)
    c_qnc = REAL(qnc, c_double)
    c_qnr = REAL(qnr, c_double)
    c_qni = REAL(qni, c_double)
    c_qns = REAL(qns, c_double)
    c_qng = REAL(qng, c_double)
    c_qna = REAL(qna, c_double)
    
    ! ------------------------------
    ! 3) Allocate and copy 2D arrays
    ! ------------------------------
    ALLOCATE(c_xland(ims:ime, jms:jme))
    ALLOCATE(c_ivgtyp(ims:ime, jms:jme))
    ALLOCATE(c_xlat(ims:ime, jms:jme))
    ALLOCATE(c_xlong(ims:ime, jms:jme))
    
    c_xland = REAL(xland, c_double)
    c_ivgtyp = INT(ivgtyp, c_int)
    c_xlat = REAL(xlat, c_double)
    c_xlong = REAL(xlong, c_double)
    
    ! ------------------------------
    ! 4) Allocate and copy 4D arrays
    ! ------------------------------
    ALLOCATE(c_chem_new(ims:ime, kms:kme, jms:jme, n_chem))
    ALLOCATE(c_sbmradar(ims:ime, kms:kme, jms:jme, num_sbmradar))
    
    c_chem_new = REAL(chem_new, c_double)
    c_sbmradar = REAL(sbmradar, c_double)
    
    ! ------------------------------
    ! 5) Handle optional arrays
    ! ------------------------------
    IF (PRESENT(rainnc)) THEN
      ALLOCATE(c_rainnc(ims:ime, jms:jme))
      c_rainnc = REAL(rainnc, c_double)
    END IF
    
    IF (PRESENT(rainncv)) THEN
      ALLOCATE(c_rainncv(ims:ime, jms:jme))
      c_rainncv = REAL(rainncv, c_double)
    END IF
    
    IF (PRESENT(snownc)) THEN
      ALLOCATE(c_snownc(ims:ime, jms:jme))
      c_snownc = REAL(snownc, c_double)
    END IF
    
    IF (PRESENT(snowncv)) THEN
      ALLOCATE(c_snowncv(ims:ime, jms:jme))
      c_snowncv = REAL(snowncv, c_double)
    END IF
    
    IF (PRESENT(graupelnc)) THEN
      ALLOCATE(c_graupelnc(ims:ime, jms:jme))
      c_graupelnc = REAL(graupelnc, c_double)
    END IF
    
    IF (PRESENT(graupelncv)) THEN
      ALLOCATE(c_graupelncv(ims:ime, jms:jme))
      c_graupelncv = REAL(graupelncv, c_double)
    END IF
    
    IF (PRESENT(sr)) THEN
      ALLOCATE(c_sr(ims:ime, jms:jme))
      c_sr = REAL(sr, c_double)
    END IF

    ! ------------------------------
    ! 6) Call the C++ function
    ! ------------------------------
    CALL c_fast_sbm_ml( c_w, c_u, c_v, c_th_old, &
      & c_chem_new, c_n_chem, &
      & c_itimestep, c_dt, c_dx, c_dy, &
      & c_dz8w, c_rho_phy, c_p_phy, c_pi_phy, c_th_phy, &
      & c_xland, c_domain_id, c_ivgtyp, c_xlat, c_xlong, &
      & c_qv, c_qc, c_qr, c_qi, c_qs, c_qg, c_qv_old, &
      & c_qnc, c_qnr, c_qni, c_qns, c_qng, c_qna, &
      & c_ids, c_ide, c_jds, c_jde, c_kds, c_kde, &
      & c_ims, c_ime, c_jms, c_jme, c_kms, c_kme, &
      & c_its, c_ite, c_jts, c_jte, c_kts, c_kte, &
      & c_diagflag, &
      & c_sbmradar, c_num_sbmradar, &
      & c_sbm_diagnostics, &
      & c_rainnc, c_rainncv, c_snownc, c_snowncv, &
      & c_graupelnc, c_graupelncv, c_sr )

    ! ------------------------------
    ! 7) Copy modified data back to original arrays
    ! ------------------------------
    th_old = REAL(c_th_old)
    th_phy = REAL(c_th_phy)
    qv = REAL(c_qv)
    qc = REAL(c_qc)
    qr = REAL(c_qr)
    qi = REAL(c_qi)
    qs = REAL(c_qs)
    qg = REAL(c_qg)
    qv_old = REAL(c_qv_old)
    qnc = REAL(c_qnc)
    qnr = REAL(c_qnr)
    qni = REAL(c_qni)
    qns = REAL(c_qns)
    qng = REAL(c_qng)
    qna = REAL(c_qna)
    chem_new = REAL(c_chem_new)
    sbmradar = REAL(c_sbmradar)
    
    ! Copy back optional arrays if present
    IF (PRESENT(rainnc)) THEN
      rainnc = REAL(c_rainnc)
    END IF
    
    IF (PRESENT(rainncv)) THEN
      rainncv = REAL(c_rainncv)
    END IF
    
    IF (PRESENT(snownc)) THEN
      snownc = REAL(c_snownc)
    END IF
    
    IF (PRESENT(snowncv)) THEN
      snowncv = REAL(c_snowncv)
    END IF
    
    IF (PRESENT(graupelnc)) THEN
      graupelnc = REAL(c_graupelnc)
    END IF
    
    IF (PRESENT(graupelncv)) THEN
      graupelncv = REAL(c_graupelncv)
    END IF
    
    IF (PRESENT(sr)) THEN
      sr = REAL(c_sr)
    END IF

    ! ------------------------------
    ! 8) Deallocate temporary arrays
    ! ------------------------------
    DEALLOCATE(c_w, c_u, c_v, c_th_old)
    DEALLOCATE(c_dz8w, c_rho_phy, c_p_phy, c_pi_phy, c_th_phy)
    DEALLOCATE(c_xland, c_ivgtyp, c_xlat, c_xlong)
    DEALLOCATE(c_qv, c_qc, c_qr, c_qi, c_qs, c_qg, c_qv_old)
    DEALLOCATE(c_qnc, c_qnr, c_qni, c_qns, c_qng, c_qna)
    DEALLOCATE(c_chem_new, c_sbmradar)
    
    ! Deallocate optional arrays if allocated
    IF (ALLOCATED(c_rainnc)) DEALLOCATE(c_rainnc)
    IF (ALLOCATED(c_rainncv)) DEALLOCATE(c_rainncv)
    IF (ALLOCATED(c_snownc)) DEALLOCATE(c_snownc)
    IF (ALLOCATED(c_snowncv)) DEALLOCATE(c_snowncv)
    IF (ALLOCATED(c_graupelnc)) DEALLOCATE(c_graupelnc)
    IF (ALLOCATED(c_graupelncv)) DEALLOCATE(c_graupelncv)
    IF (ALLOCATED(c_sr)) DEALLOCATE(c_sr)

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