! =============================================================================
! PYSBM API - Complete C Interface Declarations
! =============================================================================
! This file provides all C interface declarations for PYSBM functionality.
! It's designed to be portable as a single include file for static library use.
!
! Usage: include 'pysbm_api.inc'
! =============================================================================

! Autoencoder C functions
interface
    subroutine c_encoder( &
                           encoded_output, input_tensor, &
                           nx, ny, nz, &
                           input_channels, encoded_channels) bind(C, name="c_encoder_")
        import :: c_float, c_int
        real(c_float), intent(out), dimension(*) :: encoded_output
        real(c_float), intent(in), dimension(*) :: input_tensor
        integer(c_int), intent(in) :: nx, ny, nz
        integer(c_int), intent(in) :: input_channels
        integer(c_int), intent(in) :: encoded_channels
    end subroutine c_encoder

    subroutine c_decoder( &
                           decoded_output, encoded_input, &
                           nx, ny, nz, &
                           output_channels, encoded_channels) bind(C, name="c_decoder_")
        import :: c_float, c_int
        real(c_float), intent(out), dimension(*) :: decoded_output
        real(c_float), intent(in), dimension(*) :: encoded_input
        integer(c_int), intent(in) :: nx, ny, nz
        integer(c_int), intent(in) :: output_channels
        integer(c_int), intent(in) :: encoded_channels
    end subroutine c_decoder

    subroutine get_encoder_output_channels( &
                            n_chem_encoded, input_channels) bind(C, name="get_encoder_output_channels_")
        import :: c_int
        integer(c_int), intent(out) :: n_chem_encoded
        integer(c_int), intent(in) :: input_channels
    end subroutine get_encoder_output_channels

    function load_encoder_from_path(model_path) bind(C, name="load_encoder_from_path")
        import :: c_char, c_bool
        character(kind=c_char), intent(in) :: model_path(*)
        logical(c_bool) :: load_encoder_from_path
    end function load_encoder_from_path

    function load_decoder_from_path(model_path) bind(C, name="load_decoder_from_path")
        import :: c_char, c_bool
        character(kind=c_char), intent(in) :: model_path(*)
        logical(c_bool) :: load_decoder_from_path
    end function load_decoder_from_path
end interface

! ML SBM C functions
interface
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

    function load_model_from_path(model_path) bind(C, name="load_model_from_path")
        import :: c_char, c_bool
        character(kind=c_char), intent(in) :: model_path(*)
        logical(c_bool) :: load_model_from_path
    end function load_model_from_path
end interface

! PYSBM wrapper C functions
interface
    subroutine c_pysbm_wrapper(w, u, v, th_old, chem_new, n_chem, itimestep, dt, dx, dy, dz8w, rho_phy, p_phy, pi_phy, th_phy, xland, domain_id, ivgtyp, xlat, xlong, qv, qc, qr, qi, qs, qg, qv_old, qnc, qnr, qni, qns, qng, qna, ids, ide, jds, jde, kds, kde, ims, ime, jms, jme, kms, kme, its, ite, jts, jte, kts, kte, diagflag, sbmradar, num_sbmradar, sbm_diagnostics, rainnc, rainncv, snownc, snowncv, graupelnc, graupelncv, sr) bind(C, name="c_pysbm_wrapper")
        integer, intent(in) :: ids, ide, jds, jde, kds, kde
        integer, intent(in) :: ims, ime, jms, jme, kms, kme
        integer, intent(in) :: its, ite, jts, jte, kts, kte
        integer, intent(in) :: itimestep, n_chem, num_sbmradar, domain_id, sbm_diagnostics
        real, intent(in) :: dt, dx, dy
        real, intent(in) :: w(ims:ime, kms:kme, jms:jme), u(ims:ime, kms:kme, jms:jme), v(ims:ime, kms:kme, jms:jme)
        real, intent(in) :: dz8w(ims:ime, kms:kme, jms:jme), rho_phy(ims:ime, kms:kme, jms:jme), p_phy(ims:ime, kms:kme, jms:jme), pi_phy(ims:ime, kms:kme, jms:jme)
        real, intent(in) :: xland(ims:ime, jms:jme), xlat(ims:ime, jms:jme), xlong(ims:ime, jms:jme)
        integer, intent(in) :: ivgtyp(ims:ime, jms:jme)
        real, intent(inout) :: th_old(ims:ime, kms:kme, jms:jme), qv(ims:ime, kms:kme, jms:jme), qv_old(ims:ime, kms:kme, jms:jme)
        real, intent(inout) :: qc(ims:ime, kms:kme, jms:jme), qr(ims:ime, kms:kme, jms:jme), qi(ims:ime, kms:kme, jms:jme)
        real, intent(inout) :: qs(ims:ime, kms:kme, jms:jme), qg(ims:ime, kms:kme, jms:jme)
        real, intent(inout) :: qnc(ims:ime, kms:kme, jms:jme), qnr(ims:ime, kms:kme, jms:jme), qni(ims:ime, kms:kme, jms:jme)
        real, intent(inout) :: qns(ims:ime, kms:kme, jms:jme), qng(ims:ime, kms:kme, jms:jme), qna(ims:ime, kms:kme, jms:jme)
        real, intent(inout) :: th_phy(ims:ime, kms:kme, jms:jme)
        real, intent(inout) :: chem_new(ims:ime, kms:kme, jms:jme, n_chem)
        real, intent(inout) :: sbmradar(ims:ime, kms:kme, jms:jme, num_sbmradar)
        logical, intent(in) :: diagflag
        real, intent(inout) :: rainnc(ims:ime, jms:jme), rainncv(ims:ime, jms:jme), snownc(ims:ime, jms:jme)
        real, intent(inout) :: snowncv(ims:ime, jms:jme), graupelnc(ims:ime, jms:jme), graupelncv(ims:ime, jms:jme), sr(ims:ime, jms:jme)
    end subroutine c_pysbm_wrapper

    subroutine c_pysbm_hucminit_wrapper(dt, input_dir) bind(C, name="c_pysbm_hucminit_wrapper")
        import :: c_char, c_float
        real(c_float), intent(in) :: dt
        character(kind=c_char), intent(in) :: input_dir(*)
    end subroutine c_pysbm_hucminit_wrapper
end interface