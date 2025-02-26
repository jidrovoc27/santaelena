const _url = window.location.toString().split(window.location.host.toString())[1];
const cargando = '<i class="fa fa-cog fa-spin" role="status" aria-hidden="true"></i>';
const method_req = "POST";
const _enc = $('*[data-datoseguro=true]').toArray();
const headerId = '#header';
var __enc = [];
for (var i = 0; i < _enc.length; i++) {
    __enc.push($(_enc[i]).attr('name'));
}
const inputsEncrypted = __enc.join('|');
$(function () {
    $('form:not(#frmEliminar, #frmEliminar1,  #frmEliminar2, #frmVisita, #frmVisible, #frmEliPrg, #frmRespuesta, #frmGestion, #frmReactivar, #frmEliminarConComentario, #frmQuitarBestseller, #frmHacerBestseller, #frmActivarProducto, [method=GET], [method=get])').submit(function (e) {
        e.preventDefault();
        var captchaval = false;
        var bandera = true;
        const formulario = $(this)
        if ($("#g-recaptcha-response").length !== 0) {
            bandera = false;
            if (!checkRecaptcha()) {
                smoke.alert('Complete el captcha para continuar')
                return false;
            } else {
                captchaval = true;
                bandera = true;
            }
        }
        if (bandera) {
            smoke.confirm(`¿Está seguro que desea seguir con esta operación?`, function (e) {
                    if (e) {
                        const btnSubmit = $('#submit,#submit2,#submit3');
                        const error_btn = btnSubmit.html();
                        $('input').removeClass('is-invalid');
                        const pk = formulario.find('input[name=pk]').length ? parseInt(formulario.find('input[name=pk]').val()) : 0;
                        const action = formulario.find('input[name=action]').length ? formulario.find('input[name=action]').val() : false;
                        var _form = new FormData(formulario[0]);
                        if (pk !== 0) {
                            if (_form.has('pk')) {
                                _form.set('pk', pk.toString());
                            } else {
                                _form.append('pk', pk.toString());
                            }

                        }
                        if (action !== false) {
                            if (_form.has('action')) {
                                _form.set('action', action);
                            } else {
                                _form.append('action', action);
                            }
                        }
                        const listInputsEnc = inputsEncrypted.split('|');
                        for (var i = 0; i < listInputsEnc.length; i++) {
                            if (_form.has(listInputsEnc[i])) {
                                _form.set(listInputsEnc[i], doRSA(_form.get(listInputsEnc[i])));
                            }
                        }
                        $.ajax({
                            type: method_req,
                            url: _url,
                            data: _form,
                            dataType: "json",
                            enctype: formulario.attr('enctype'),
                            cache: false,
                            contentType: false,
                            processData: false,
                            beforeSend: function () {
                                btnSubmit.html(cargando);
                                btnSubmit.attr("disabled", true);
                                pantallaespera();
                            }
                        }).done(function (data) {
                            if (!data.result) {
                                if (data.to) {
                                    location = data.to;
                                } else {
                                    $('.modal').modal('hide')
                                    smoke.alert(data.mensaje)
                                }
                            } else {
                                smoke.alert(data.mensaje);
                                if (data.mensajeerror) {
                                    console.log(data.mensajeerror)
                                }
                                if (captchaval) {
                                    grecaptcha.reset();
                                }
                            }
                            btnSubmit.html(error_btn);
                            btnSubmit.attr("disabled", false);
                            $.unblockUI();
                        }).fail(function (jqXHR, textStatus, errorThrown) {
                            smoke.alert('Intentelo más tarde');
                            btnSubmit.html(error_btn);
                            btnSubmit.attr("disabled", false);
                            if (captchaval) {
                                grecaptcha.reset();
                            }
                            $.unblockUI();
                        }).always(function () {

                        });
                    }
                },
                {ok: "Continuar", cancel: "Cancelar"}
            );
        }

    });
});