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

  include 'pysbm_api.inc'

  PRIVATE
  PUBLIC FAST_SBM, FAST_HUCMINIT

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
    ! (F) Autoencoder Local Variables
    ! ------------------------------

    integer, parameter :: nkr = 33, nkr_encoded = 34, &
                              p_ff1i01 =   2, p_ff1i33 =  34,    &
                              p_ff8i01 = 101, p_ff8i43 = 143
    REAL :: ff1(ime - ims + 1, kme - kms + 1, jme - jms + 1, nkr_encoded)
    REAL :: ff1_decoded(ime - ims + 1, kme - kms + 1, jme - jms + 1, nkr)
    integer :: i, j, k, kr, krr
    integer :: Nx, Ny, Nz
    Nx = ime - ims + 1
    Nz = kme - kms + 1
    Ny = jme - jms + 1
    

    do k = 1, Nz
    do j = 1, Ny
    do i = 1, Nx
        ! drops
        krr = 0
        do kr = p_ff1i01, p_ff1i33
            krr = krr + 1
            ff1_decoded(i,k,j,krr) = chem_new(i + ims - 1, k + kms - 1,j + jms - 1,kr)
        end do
        
    end do
    end do
    end do

    ! --- AE workflow: decode -> pysbm -> encode ---
    ! 1. Add Reconstruction
    CALL c_encoder(ff1, ff1_decoded, Nx, Ny, Nz, nkr, nkr_encoded)
    CALL c_decoder(ff1_decoded, ff1, Nx, Ny, Nz, nkr, nkr_encoded)

    do k = 1, Nz
    do j = 1, Ny
    do i = 1, Nx
        ! drops
        krr = 0
        do kr = p_ff1i01, p_ff1i33
            krr = krr + 1
            chem_new(i + ims - 1, k + kms - 1,j + jms - 1,kr) = ff1_decoded(i,k,j,krr)
        end do
        
    end do
    end do
    end do

    ! 2. Run core SBM (pysbm)
    ! NOTE: The arguments here must match the actual pysbm signature
    CALL c_pysbm_wrapper( w,u,v,th_old,                                &
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

    RETURN
  END SUBROUTINE FAST_SBM

  !----------------------------------------------------------------------
  ! 3) FAST_HUCMINIT => remains no-op
  !----------------------------------------------------------------------
  SUBROUTINE FAST_HUCMINIT(dt)
    use iso_c_binding
    IMPLICIT NONE

    REAL, INTENT(IN) :: dt
    CHARACTER(len=256) :: input_dir, encoder_path, decoder_path
    LOGICAL :: success

    input_dir = "SBM_input_33"  ! or set as needed


    CALL c_pysbm_hucminit_wrapper(dt, input_dir)
    
    encoder_path = "../models/encoder_model_33.pt"
    decoder_path = "../models/decoder_model_33.pt"
    PRINT *, "Encoder path: ", encoder_path
    PRINT *, "Decoder path: ", decoder_path
    
    success = load_encoder_from_path(trim(encoder_path) // c_null_char)
    if (.not. success) then
        PRINT *, "ERROR: Failed to load encoder model from path: ", trim(encoder_path)
    else
        PRINT *, "SUCCESS: Encoder model loaded successfully"
    end if
    
    success = load_decoder_from_path(trim(decoder_path) // c_null_char)
    if (.not. success) then
        PRINT *, "ERROR: Failed to load decoder model from path: ", trim(decoder_path)
    else
        PRINT *, "SUCCESS: Decoder model loaded successfully"
    end if

    RETURN
  END SUBROUTINE FAST_HUCMINIT

END MODULE module_mp_fast_sbm



#endif