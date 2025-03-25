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
    SUBROUTINE c_fast_sbm_ml( n_chem, nbatch, in_data, out_data ) BIND(C, name="c_fast_sbm_ml_")
      USE, INTRINSIC :: iso_c_binding
      IMPLICIT NONE
      INTEGER(c_int), INTENT(IN) :: n_chem, nbatch
      REAL(c_double), INTENT(IN)  :: in_data(*)
      REAL(c_double), INTENT(OUT) :: out_data(*)
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
    ! Local scalars for flattening
    ! ------------------------------
    INTEGER :: nx, ny, nz, nbatch
    INTEGER(c_int) :: c_nchem, c_nbatch
    REAL(c_double), ALLOCATABLE :: c_in(:,:), c_out(:,:)

    ! 1) Determine domain sizes
    nx = ide - ids + 1
    ny = jde - jds + 1
    nz = kde - kds + 1
    nbatch = nx * ny * nz

    c_nchem  = n_chem
    c_nbatch = nbatch

    ! 2) Flatten chem_new => shape [n_chem, nbatch]
    ALLOCATE(c_in(n_chem, nbatch), c_out(n_chem, nbatch))
    c_in = RESHAPE( chem_new, SHAPE=[n_chem, nbatch] )

    ! 3) Call the minimal C function
    CALL c_fast_sbm_ml( c_nchem, c_nbatch, c_in, c_out )

    ! 4) Copy back
    chem_new = RESHAPE( c_out, SHAPE(chem_new) )

    ! 5) Deallocate
    DEALLOCATE(c_in, c_out)

    ! The rest is no-op
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