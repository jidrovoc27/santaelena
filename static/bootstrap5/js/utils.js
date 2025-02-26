<!----------------- JQUERY FUNCIONAL-------------------->
jQuery.browser = {};
(function () {
    jQuery.browser.msie = false;
    jQuery.browser.version = 0;
    if (navigator.userAgent.match(/MSIE ([0-9]+)\./)) {
        jQuery.browser.msie = true;
        jQuery.browser.version = RegExp.$1;
    }
})();

<!----------------- CARGA DE CRFTOKEN PARA CONSULTAS AJAX-------------------->
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

<!----------------- CARGAS DEL DOOM -------------------->
$(function () {
<!----------------- RECUPERACIÓN DE VARIABLES Y TRATADO SEGÚN EXISTENCIA-------------------->
    let persona = localStorage.getItem("tiene_persona");
    let check_session = localStorage.getItem("tiene_check_session");
    if (persona && check_session) {
        chequearsesion = function () {
            $.ajax({
                type: "POST",
                url: "/api",
                data: {'a': 'checksession'},
                success: function (data) {
                    if (data.result == 'ok') {
                        if (data.nuevasesion) {
                            bloqueointerface();
                            location.href = '/logout';
                        }
                    }
                },
                dataType: "json"
            });
        };
        setInterval(chequearsesion, 60000);
    }
    if (persona) {
         $(".periodoselector").click(function () {
                var pid = $(this).attr('pid');
                bloqueointerface();
                $.ajax({
                    type: "POST",
                    url: "/",
                    data: {'action': 'periodofis', 'id': pid},
                    success: function (data) {
                        if (data.result == 'ok') {
                            location.href = location.pathname;
                        } else {
                            $.unblockUI();
                            smoke.alert("Error al cambiar de periodo");
                        }
                    },
                    error: function () {
                        $.unblockUI();
                        smoke.alert("Error al cambiar de periodo");
                    },
                    dataType: "json"
                });
            });
        $('.viewNotification_b').click(function () {
                var id = $(this).attr('id');
                var _href = $(this).attr('_href');
                bloqueointerface();
                $.ajax({
                    type: "POST",
                    url: "/notificacion",
                    data: {'action': 'ViewedNotification', 'id': id},
                    success: function (data) {
                        $.unblockUI();
                        if (data.result == 'ok') {
                            window.open(_href, '_blank');
                            location.reload()
                        } else {
                            mensajeWarning(data.mensaje);
                        }
                    },
                    error: function () {
                        $.unblockUI();
                        mensajeWarning("Error de conexión.");
                    },
                    dataType: "json"
                });
                });
        logout = function() {
            bloqueointerface();
            localStorage.clear();
            $.ajax({
                type: "POST",
                url: "/api",
                data: {'a': 'logout'},
                headers: {
                    "X-CSRFToken": csrftoken // Incluir el token CSRF en los encabezados de la solicitud
                },
                success: function (data) {
                    if (data.result == 'ok') {
                        location.href = data.url;
                    } else {
                        logout();
                    }
                },
                error: function () {
                    logout();
                },
                dataType: "json"
            });
        };
        $('.logoutuser').click(function () {
            logout();
        });
    }

<!----------------- EJECUCIÓN DE FUNCIONES SEGÚN CLASES O IDS -------------------->
    $('.bloqueo_pantalla').click(function () {
        bloqueointerface();
    })
});

<!----------------- FUNCIONES REUTILIZABLES -------------------->
function bloqueointerface() {
    $.blockUI({
        message: '<span class="spinner-border text-secondary" role="status" aria-hidden="true" style="width: 5rem; height: 5rem;"></span>',
        css: {
            backgroundColor: 'transparent',
            border: '0',
            zIndex: 9999999
        },
        overlayCSS: {
            backgroundColor: 'rgba(17,17,17,0.23)',
            opacity: 0.8,
            zIndex: 9999990
        }
    });
}

function soloNumerosValor(e) {
    key = e.keyCode || e.which;
    teclado = String.fromCharCode(key);
    letras = "01234567891.";
    if (letras.indexOf(teclado) === -1) {
        return false;
    }
}

function MenuFijo(){
    var altura=$('.caja-menu').offset().top;
    $(window).on('scroll', function (){
        if ( $(window).scrollTop() > altura){
            $('.caja-menu').addClass('caja-menu-flotante');
        }else{
            $('.caja-menu').removeClass('caja-menu-flotante');
        }
    })
}

<!----------------- MENSAJES FLOTANTES SWEETALERT 2 -------------------->
function mensajeSuccess(titulo, mensaje) {
    Swal.fire(titulo, mensaje, 'success')
}

function mensajeWarning(titulo, mensaje) {
    Swal.fire(titulo, mensaje, 'warning')
}

function mensajeDanger(titulo, mensaje) {
    Swal.fire(titulo, mensaje, 'error')
}

function alertaSuccess(mensaje, time = 5000) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        type: 'success',
        title: mensaje,
        showConfirmButton: false,
        timer: time
    })
}

function alertaWarning(mensaje, time = 5000) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        type: 'warning',
        title: mensaje,
        showConfirmButton: false,
        timer: time
    })
}

function alertaDanger(mensaje, time = 5000) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        type: 'error',
        title: mensaje,
        showConfirmButton: false,
        timer: time
    })
}

function alertaInfo(mensaje, time = 5000) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        type: 'info',
        title: mensaje,
        showConfirmButton: false,
        timer: time
    })
}

Confirm = {
            question: function (question, fun_yes/*=null*/, fun_no/*=null*/) {
                var $popup = $('#modalConfirm');

                $popup.modal({backdrop: 'static', keyboard: false}).modal('show');

                $('.modal-body p', $popup).html(question);

                $('.action_yes', $popup).off('click').on('click', function () {
                    if (typeof fun_yes != 'undefined') {
                        fun_yes();
                    }
                    $popup.modal('hide');
                });

                $('.action_not', $popup).off('click').on('click', function () {
                    if (typeof fun_no != 'undefined') {
                        fun_no();
                    }
                    $popup.modal('hide');
                });
            },
            ajax: function (aData, fun_yes/*=null*/, fun_no/*=null*/) {
                var d = {"action": "deleteView"}
                $.each(aData, function (index, value) {
                    d[index] = value
                });
                aData = d
                bloqueointerface();
                var $popup = $('#modalConfirmAjax');
                $.ajax({
                    type: "GET",
                    url: "/data",
                    data: aData,
                    success: function (data) {
                        if (data.result == 'ok') {
                            $('.modal-body', $popup).html(data.html);
                            var h = $(window).height() - 350;
                            $popup.modal({backdrop: 'static', keyboard: false, width: "60%", height: h}).modal('show');
                            $('.action_yes', $popup).off('click').on('click', function () {
                                if (typeof fun_yes != 'undefined') {
                                    fun_yes();
                                }
                                $popup.modal('hide');
                            });

                            $('.action_not', $popup).off('click').on('click', function () {
                                if (typeof fun_no != 'undefined') {
                                    fun_no();
                                }
                                $popup.modal('hide');
                            });
                        } else {
                            NotificationJG.error(data.mensaje);
                        }
                        $.unblockUI();
                    },
                    error: function () {
                        $.unblockUI();
                        NotificationJG.error("Error al enviar los datos.");
                    },
                    dataType: "json",
                });
            },
        };
