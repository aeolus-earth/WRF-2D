! Interface declarations for PYSBM C wrapper functions
! These functions are implemented in pysbm_c_wrappers.f90 and call the actual PYSBM module procedures

interface
  ! C interface for autoencoder functions
  subroutine c_encoder(encoded_output, input_tensor, nx, ny, nz, input_channels, encoded_channels) bind(C, name="c_encoder_")
    use iso_c_binding
    real(c_float), intent(out), dimension(*) :: encoded_output
    real(c_float), intent(in), dimension(*) :: input_tensor
    integer(c_int), intent(in) :: nx, ny, nz
    integer(c_int), intent(in) :: input_channels, encoded_channels
  end subroutine c_encoder

  subroutine c_decoder(decoded_output, encoded_input, nx, ny, nz, output_channels, encoded_channels) bind(C, name="c_decoder_")
    use iso_c_binding
    real(c_float), intent(out), dimension(*) :: decoded_output
    real(c_float), intent(in), dimension(*) :: encoded_input
    integer(c_int), intent(in) :: nx, ny, nz
    integer(c_int), intent(in) :: output_channels, encoded_channels
  end subroutine c_decoder

  function load_encoder_from_path(model_path) bind(C, name="load_encoder_from_path")
    use iso_c_binding
    character(kind=c_char), intent(in) :: model_path(*)
    logical(c_bool) :: load_encoder_from_path
  end function load_encoder_from_path

  function load_decoder_from_path(model_path) bind(C, name="load_decoder_from_path")
    use iso_c_binding
    character(kind=c_char), intent(in) :: model_path(*)
    logical(c_bool) :: load_decoder_from_path
  end function load_decoder_from_path

  ! C interface for wrapped PYSBM functions
  subroutine c_pysbm_wrapper(w, u, v, th_old, chem_new, n_chem, itimestep, dt, dx, dy, dz8w, rho_phy, p_phy, pi_phy, th_phy, xland, domain_id, ivgtyp, xlat, xlong, qv, qc, qr, qi, qs, qg, qv_old, qnc, qnr, qni, qns, qng, qna, ids, ide, jds, jde, kds, kde, ims, ime, jms, jme, kms, kme, its, ite, jts, jte, kts, kte, diagflag, sbmradar, num_sbmradar, sbm_diagnostics, rainnc, rainncv, snownc, snowncv, graupelnc, graupelncv, sr) bind(C, name="c_pysbm_wrapper")
    use iso_c_binding
    integer(c_int), intent(in) :: ids, ide, jds, jde, kds, kde
    integer(c_int), intent(in) :: ims, ime, jms, jme, kms, kme
    integer(c_int), intent(in) :: its, ite, jts, jte, kts, kte
    integer(c_int), intent(in) :: itimestep, n_chem, num_sbmradar, domain_id, sbm_diagnostics
    real(c_float), intent(in) :: dt, dx, dy
    real(c_float), intent(in), dimension(*) :: u, v, w, dz8w, rho_phy, p_phy, pi_phy
    real(c_float), intent(in), dimension(*) :: xland, xlat, xlong
    integer(c_int), intent(in), dimension(*) :: ivgtyp
    real(c_float), intent(inout), dimension(*) :: th_old, qv, qv_old, qc, qr, qi, qs, qg, qnc, qnr, qni, qns, qng, qna, th_phy
    real(c_float), intent(inout), dimension(*) :: chem_new
    real(c_float), intent(inout), dimension(*) :: sbmradar
    logical(c_bool), intent(in) :: diagflag
    real(c_float), intent(inout), dimension(*) :: rainnc, rainncv, snownc, snowncv, graupelnc, graupelncv, sr
  end subroutine c_pysbm_wrapper

  subroutine c_pysbm_hucminit_wrapper(dt, input_dir) bind(C, name="c_pysbm_hucminit_wrapper")
    use iso_c_binding
    real(c_float), intent(in) :: dt
    character(kind=c_char), intent(in) :: input_dir(*)
  end subroutine c_pysbm_hucminit_wrapper
end interface