$(function () {
    var _url = window.location.toString().split(window.location.host.toString())[1];
    var cargando = '<i class="fa fa-cog fa-spin" role="status" aria-hidden="true"></i>';
    var error_btn2 = '<i class="fa fa-check-circle" role="status" aria-hidden="true"></i> Guardar';
    var method_req = "POST";
    var _enc = $('*[data-datoseguro=true]').toArray();
    var headerId = '#header';
    var __enc = [];
    for (var i = 0; i < _enc.length; i++) {
        __enc.push($(_enc[i]).attr('name'));
    }
    var inputsEncrypted = __enc.join('|');

    $('form:not([method=GET], [method=get])').submit(function (e) {
        e.preventDefault();
        var formulario = $(this);
        var btnSubmit = $('#submit,#submit2,#submit3');
        var error_btn = btnSubmit.html();
        $('input, textarea, select').removeClass('is-invalid');
        var pk = $(this).find('input[name=pk]').length ? parseInt($(this).find('input[name=pk]').val()) : 0;
        var action = $(this).find('input[name=action]').length ? $(this).find('input[name=action]').val() : false;
        var _url = formulario.find('input[name=urlsubmit]').length ? formulario.find('input[name=urlsubmit]').val() : window.location.toString().split(window.location.host.toString())[1];
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
        try {
            _form.append("lista_items1", JSON.stringify(lista_items1));
        } catch (err) {
            console.log(err.message);
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
                bloqueointerface();
            }
        }).done(function (data) {
            if (!data.result) {
                if (data.modalname) {
                    $('#' + data.modalname).modal('hide');
                } else {
                    $(".modal").modal('hide');
                }
                if (data.to) {
                    if (data.modalsuccess) {
                        $.unblockUI();
                        $('#textpanelmensaje').html(data.mensaje);
                        $('#returnpanelmensaje').attr("href", data.to);
                        $('#waitpanelmensaje').modal({backdrop: 'static'}).modal('show');
                    } else {
                        location = data.to;
                    }
                } else if (data.cerrar) {
                    $.unblockUI();
                    Swal.fire(data.mensaje, '', 'success')
                } else {
                    if (data.noreload) {
                        $.unblockUI();
                        mensajeSuccess(data.mensaje);
                    } else {
                        location.reload();
                    }

                }
            } else {
                if (data.form) {
                    data.form.forEach(function (val, indx) {
                        var keys = Object.keys(val);
                        keys.forEach(function (val1, indx1) {
                            $("#id_" + val1).addClass("is-invalid");
                            $("#errorMessage" + val1).html(val[val1]);
                        });
                    });
                }
                alertaDanger(data.mensaje);
                btnSubmit.html(error_btn2);
                btnSubmit.attr("disabled", false);
                $.unblockUI();
            }
        }).fail(function (jqXHR, textStatus, errorThrown) {
            btnSubmit.html(error_btn2);
            btnSubmit.attr("disabled", false);
            $.unblockUI();
        }).always(function () {

        });
    });
});

