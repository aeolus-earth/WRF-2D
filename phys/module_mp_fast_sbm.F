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

MODULE module_mp_fast_sbm

  IMPLICIT NONE
  PRIVATE
  PUBLIC  FAST_SBM, FAST_HUCMINIT

CONTAINS

  !------------------------------------------------------------------
  ! Minimal stub for FAST_SBM:
  !  - Has the same argument list as the real code
  !  - All dummy arguments declared so it compiles
  !  - Does nothing in the body
  !------------------------------------------------------------------
  SUBROUTINE FAST_SBM ( w,u,v,th_old,                                &
      &                 chem_new,n_chem,                            &
      &                 itimestep,DT,DX,DY,                         &
      &                 dz8w,rho_phy,p_phy,pi_phy,th_phy,           &
      &                 xland,domain_id,ivgtyp,xlat,xlong,          &
      &                 QV,QC,QR,QI,QS,QG,QV_OLD,                   &
      &                 QNC,QNR,QNI,QNS,QNG,QNA,                    &
      &                 ids,ide, jds,jde, kds,kde,                  &
      &                 ims,ime, jms,jme, kms,kme,                  &
      &                 its,ite, jts,jte, kts,kte,                  &
      &                 diagflag,                                   &
      &                 sbmradar,num_sbmradar,                      &
      &                 sbm_diagnostics,                            &
      &                 RAINNC,RAINNCV,SNOWNC,SNOWNCV,              &
      &                 GRAUPELNC,GRAUPELNCV,SR)

    IMPLICIT NONE

    ! 1) Indices and scalars
    INTEGER, INTENT(IN) :: IDS,IDE,JDS,JDE,KDS,KDE
    INTEGER, INTENT(IN) :: IMS,IME,JMS,JME,KMS,KME
    INTEGER, INTENT(IN) :: ITS,ITE,JTS,JTE,KTS,KTE
    INTEGER, INTENT(IN) :: itimestep, n_chem, num_sbmradar, domain_id
    INTEGER, INTENT(IN) :: sbm_diagnostics
    REAL,  INTENT(IN)   :: DT, DX, DY
    LOGICAL, OPTIONAL, INTENT(IN) :: diagflag

    ! 2) 3D fields
    REAL, INTENT(IN)  :: w      (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: u      (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: v      (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: dz8w   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: rho_phy(ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: p_phy  (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(IN)  :: pi_phy (ims:ime, kms:kme, jms:jme)

    REAL, INTENT(IN)  :: xland (ims:ime, jms:jme)
    INTEGER, INTENT(IN):: ivgtyp(ims:ime, jms:jme)
    REAL, INTENT(IN)   :: xlat  (ims:ime, jms:jme)
    REAL, INTENT(IN)   :: xlong (ims:ime, jms:jme)

    ! 3) INOUT arrays for microphysics
    REAL, INTENT(INOUT) :: th_old (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: th_phy (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: chem_new (ims:ime, kms:kme, jms:jme, n_chem)
    REAL, INTENT(INOUT) :: sbmradar (ims:ime, kms:kme, jms:jme, num_sbmradar)

    REAL, INTENT(INOUT) :: QV    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QC    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QR    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QI    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QS    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QG    (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QV_OLD(ims:ime, kms:kme, jms:jme)

    REAL, INTENT(INOUT) :: QNC   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QNR   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QNI   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QNS   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QNG   (ims:ime, kms:kme, jms:jme)
    REAL, INTENT(INOUT) :: QNA   (ims:ime, kms:kme, jms:jme)

    ! Optional 2D accumulators
    REAL, INTENT(INOUT), OPTIONAL :: RAINNC   (ims:ime,jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: RAINNCV  (ims:ime,jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: SNOWNC   (ims:ime,jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: SNOWNCV  (ims:ime,jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: GRAUPELNC (ims:ime,jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: GRAUPELNCV(ims:ime,jms:jme)
    REAL, INTENT(INOUT), OPTIONAL :: SR(ims:ime,jms:jme)

    ! Body of stub: do nothing
    RETURN
  END SUBROUTINE FAST_SBM

  !-----------------------------------------------------------------------
  ! Minimal stub for FAST_HUCMINIT(DT):
  !   - Only uses what's needed to compile & print a message
  !   - Must match the signature:  FAST_HUCMINIT(DT)
  !-----------------------------------------------------------------------
  SUBROUTINE FAST_HUCMINIT(DT)
    IMPLICIT NONE

    ! The original snippet used real(kind=r4size) for DT.
    REAL, INTENT(IN) :: DT

    RETURN
  END SUBROUTINE FAST_HUCMINIT

END MODULE module_mp_fast_sbm


#endif