# -*- coding: UTF-8 -*-
import json
import sys
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import get_template

#from decorators import secure_module, last_access
from administrativo.forms import ModuloForm, ModuloGrupoForm, ModuloCategoriaForm, GrupoPermisoForm
from administrativo.commonviews import adduserdata
from administrativo.funciones import MiPaginador, puede_realizar_accion
from administrativo.models import Modulo, ModuloGrupo, CategoriaModulo
from django.contrib.auth.models import Permission


@login_required(redirect_field_name='ret', login_url='/loginsagest')
#@secure_module
# @last_access

@transaction.atomic()
def view(request):
    data = {}
    adduserdata(request, data)
    persona = data['persona']
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'addmodulo':
            try:
                f = ModuloForm(request.POST)
                if f.is_valid():
                    modulo = Modulo(nombre=f.cleaned_data['nombre'],
                                    orden=f.cleaned_data['orden'],
                                    url=f.cleaned_data['url'],
                                    icono=f.cleaned_data['icono'],
                                    descripcion=f.cleaned_data['descripcion'],
                                    activo=f.cleaned_data['activo'],
                                    administrativo=f.cleaned_data['administrativo'])
                    modulo.save(request)
                    for ca in f.cleaned_data['categoria']:
                        modulo.categoria.add(ca)
                    #log(u'Adicionó Modulo: %s' % modulo, request, "add")
                    return JsonResponse({"result": False}, safe=False)
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                linea_ = sys.exc_info()[-1].tb_lineno
                return JsonResponse({"result": True,'modalsuccess': True, "mensaje": f"{ex} {linea_}"}, safe=False)

        if action == 'editmodulo':
            try:
                f = ModuloForm(request.POST)
                if f.is_valid():
                    modulo = Modulo.objects.get(pk=request.POST['id'])
                    modulo.nombre = f.cleaned_data['nombre']
                    modulo.orden = f.cleaned_data['orden']
                    modulo.url = f.cleaned_data['url']
                    modulo.icono = f.cleaned_data['icono']
                    modulo.descripcion = f.cleaned_data['descripcion']
                    modulo.activo = f.cleaned_data['activo']
                    modulo.administrativo = f.cleaned_data['administrativo']
                    modulo.save(request)
                    modulo.categoria.clear()
                    for ca in f.cleaned_data['categoria']:
                        modulo.categoria.add(ca)
                    #log(u'Editó Modulo: %s' % modulo, request, "edit")
                    return JsonResponse({"result": False}, safe=False)
                else:
                     raise NameError('Error')
            except Exception as ex:
                linea_ = sys.exc_info()[-1].tb_lineno
                transaction.set_rollback(True)
                return JsonResponse({"result": True, 'modalsuccess': True, "mensaje": f"{ex} {linea_}"}, safe=False)

        if action == 'deletemodulo':
            try:
                modulo = Modulo.objects.get(pk=request.POST['id'])
                modulo.status = False
                modulo.save(request)
                #log(u'Eliminó Modulo: %s' % modulo, request, "del")
                return JsonResponse({"error": False}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, 'modalsuccess': True, "mensaje": "Intentelo mas tarde."}, safe=False)

        if action == 'addcategoria':
            try:
                f = ModuloCategoriaForm(request.POST)
                if f.is_valid():
                    modulo = CategoriaModulo(nombre=f.cleaned_data['nombre'], orden=f.cleaned_data['orden'],
                                             icono=f.cleaned_data['icono'])
                    modulo.save(request)
                    #log(u'Adicionó Modulo Categoria: %s' % modulo, request, "add")
                    return JsonResponse({"result": False}, safe=False)
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True,'modalsuccess': True, "mensaje": "Intentelo mas tarde."}, safe=False)

        if action == 'editcategoria':
            try:
                f = ModuloCategoriaForm(request.POST)
                if f.is_valid():
                    modulo = CategoriaModulo.objects.get(pk=request.POST['id'])
                    modulo.nombre = f.cleaned_data['nombre']
                    modulo.icono = f.cleaned_data['icono']
                    modulo.orden = f.cleaned_data['orden']
                    modulo.save(request)
                    #log(u'Editó Modulo Categoria: %s' % modulo, request, "edit")
                    return JsonResponse({"result": False}, safe=False)
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, 'modalsuccess': True, "mensaje": "Intentelo mas tarde."}, safe=False)

        if action == 'deletecategoria':
            try:
                modulo = CategoriaModulo.objects.get(pk=request.POST['id'])
                modulo.status = False
                modulo.save(request)
                #log(u'Eliminó Modulo Categoria: %s' % modulo, request, "del")
                return JsonResponse({"error": False}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, 'modalsuccess': True, "mensaje": "Intentelo mas tarde."}, safe=False)

        if action == 'loadDataTable':
            try:
                txt_filter = request.POST['sSearch'] if request.POST['sSearch'] else ''
                limit = int(request.POST['iDisplayLength']) if request.POST['iDisplayLength'] else 25
                offset = int(request.POST['iDisplayStart']) if request.POST['iDisplayStart'] else 0
                aaData = []
                tCount = 0
                gruposmodulos = ModuloGrupo.objects.filter(status=True).order_by('nombre')
                if not persona.usuario.is_staff:
                    gruposmodulos = gruposmodulos.filter(status=True)
                if txt_filter:
                    search = txt_filter.strip()
                    gruposmodulos = gruposmodulos.filter(Q(nombre__icontains=search) | Q(descripcion__icontains=search))
                tCount = gruposmodulos.count()
                if offset == 0:
                    rows = gruposmodulos[offset:limit]
                else:
                    rows = gruposmodulos[offset:offset + limit]
                aaData = []
                for row in rows:
                    grupos = []
                    for g in row.groups():
                        grupos.append({"id": g.id,
                                       "nombre": g.name,
                                       })
                    modulos = []
                    for m in row.modules():
                        modulos.append({"id": m.id,
                                        "nombre": m.nombre,
                                        "activo": m.activo,
                                        })
                    aaData.append([row.id,
                                   {"nombre": row.nombre,
                                    "descripcion": row.descripcion,
                                    },
                                   {"id": row.id,
                                    "total": len(grupos),
                                    "grupos": grupos,
                                    },
                                   {"id": row.id,
                                    "total": len(modulos),
                                    "modulos": modulos,
                                    },
                                   {"id": row.id,
                                    "nombre": row.nombre,
                                    },
                                   ])
                return JsonResponse({"result": "ok", "data": aaData, "iTotalRecords": tCount, "iTotalDisplayRecords": tCount})
            except Exception as ex:
                return JsonResponse({"result": "bad", "mensaje": u"Error al cargar los datos. %s" % ex.__str__(), "data": [], "iTotalRecords": 0, "iTotalDisplayRecords": 0})

        if action == 'saveModuleGrupo':
            try:
                id = int(request.POST['id']) if 'id' in request.POST and request.POST['id'] and int(request.POST['id']) != 0 else None
                typeForm = 'edit' if id else 'new'
                f = ModuloGrupoForm(request.POST)
                f.deleteFields()
                if not f.is_valid():
                    # f.addErrors(f.errors.get_json_data(escape_html=True))
                    raise NameError(u"Debe ingresar la información en todos los campos")
                if typeForm == 'new':
                    puede_realizar_accion(request, 'bd.puede_agregar_grupos_modulos')
                    if ModuloGrupo.objects.filter(nombre=f.cleaned_data['nombre']).exists():
                        raise NameError(u"Nombre debe ser único")

                    mg = ModuloGrupo(nombre=f.cleaned_data['nombre'],
                                     descripcion=f.cleaned_data['descripcion'],
                                     prioridad=0
                                     )
                    mg.save(request)
                    if 'moduloss' in request.POST:
                        moduloss = json.loads(request.POST['moduloss'])
                        modulos = Modulo.objects.filter(pk__in=moduloss)
                        for modulo in modulos:
                            mg.modulos.add(modulo)
                    if 'gruposs' in request.POST:
                        gruposs = json.loads(request.POST['gruposs'])
                        grupos = Group.objects.filter(pk__in=gruposs)
                        for grupo in grupos:
                            mg.grupos.add(grupo)

                    #log(u'Aciciono grupo de modulo: %s' % mg, request, "add")
                else:
                    puede_realizar_accion(request, 'bd.puede_modificar_grupos_modulos')
                    if not ModuloGrupo.objects.filter(pk=id).exists():
                        raise NameError(u"No existe formulario a editar")
                    if ModuloGrupo.objects.filter(nombre=f.cleaned_data['nombre']).exclude(pk=id).exists():
                        raise NameError(u"Nombre debe ser única")
                    mg = ModuloGrupo.objects.get(pk=id)
                    mg.nombre = f.cleaned_data['nombre']
                    mg.descripcion = f.cleaned_data['descripcion']
                    mg.save(request)
                    if 'moduloss' in request.POST:
                        moduloss = json.loads(request.POST['moduloss'])
                        moduloss = [int(x) for x in moduloss]
                        moduloss_aux = mg.modulos.all()
                        for m in moduloss_aux:
                            if not m.id in moduloss:
                                mg.modulos.remove(m)
                                m.save()
                        for modulo in Modulo.objects.filter(pk__in=moduloss):
                            mg.modulos.add(modulo)
                    if 'gruposs' in request.POST:
                        gruposs = json.loads(request.POST['gruposs'])
                        gruposs = [int(x) for x in gruposs]
                        gruposs_aux = mg.grupos.all()
                        for g in gruposs_aux:
                            if not g.id in gruposs:
                                mg.grupos.remove(g)
                                g.save()
                        for grupo in Group.objects.filter(pk__in=gruposs):
                            mg.grupos.add(grupo)
                    #log(u'Edito grupo de modulo: %s' % mg, request, "edit")
                return JsonResponse({"result": "ok", "mensaje": u"Se guardo correctamente el grupo de modulo"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar el grupo de modulo. %s" % ex.__str__()})

        if action == 'deleteModuleGrupo':
            try:
                puede_realizar_accion(request, 'bd.puede_eliminar_grupos_modulos')
                if not 'id' in request.POST or not request.POST['id']:
                    raise NameError(u"No se encontro registro a eliminar")
                object_id = int(request.POST['id'])
                if not ModuloGrupo.objects.filter(pk=object_id).exists():
                    raise NameError(u"No se encontro registro a eliminar")
                eModuloGrupo = ModuloGrupo.objects.get(pk=object_id)
                #log(u'Elimino grupo de modulo: %s' % eModuloGrupo, request, "del")
                eModuloGrupo.delete()
                return JsonResponse({"result": "ok", "mensaje": u"Se elimino correctamente el grupo de modulo"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al eliminar el grupo de modulo. %s" % ex.__str__()})

        if action == 'loadDataTableGroups':
            try:
                txt_filter = request.POST['sSearch'] if request.POST['sSearch'] else ''
                limit = int(request.POST['iDisplayLength']) if request.POST['iDisplayLength'] else 25
                offset = int(request.POST['iDisplayStart']) if request.POST['iDisplayStart'] else 0
                tCount = 0
                grupos = Group.objects.filter().order_by('name')
                if txt_filter:
                    search = txt_filter.strip()
                    grupos = grupos.filter(Q(name__icontains=search))
                tCount = grupos.count()
                if offset == 0:
                    rows = grupos[offset:limit]
                else:
                    rows = grupos[offset:offset + limit]
                aaData = []
                for row in rows:
                    modulosgrupos = []
                    if ModuloGrupo.objects.filter(grupos__in=Group.objects.filter(pk=row.id)).exists():
                        modulos = []
                        for mg in ModuloGrupo.objects.filter(grupos__in=Group.objects.filter(pk=row.id)):
                            for m in mg.modulos.all():
                                modulos.append({"id": m.id,
                                                "nombre": m.nombre,
                                                "activo": m.activo,
                                                "descripcion": m.descripcion})

                            modulosgrupos.append({"id": mg.id,
                                                  "nombre": mg.nombre,
                                                  "modulos": modulos
                                                  })
                    aaData.append([row.id,
                                   row.name,
                                   modulosgrupos,
                                   {"id": row.id,
                                    "name": row.name,
                                    },
                                   ])
                return JsonResponse({"result": "ok", "data": aaData, "iTotalRecords": tCount, "iTotalDisplayRecords": tCount})
            except Exception as ex:
                return JsonResponse({"result": "bad", "mensaje": u"Error al cargar los datos. %s" % ex.__str__(), "data": [], "iTotalRecords": 0, "iTotalDisplayRecords": 0})

        if action == 'deleteGroup':
            try:
                puede_realizar_accion(request, 'bd.puede_eliminar_grupo')
                if not 'id' in request.POST or not request.POST['id']:
                    raise NameError(u"No se encontro registro a eliminar")
                object_id = int(request.POST['id'])
                if not Group.objects.filter(pk=object_id).exists():
                    raise NameError(u"No se encontro registro a eliminar")
                eGroup = Group.objects.get(pk=object_id)
                #log(u'Elimino grupo: %s' % eGroup, request, "del")
                eGroup.delete()
                return JsonResponse({"result": "ok", "mensaje": u"Se elimino correctamente el grupo"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al eliminar el grupo. %s" % ex.__str__()})

        if action == 'saveGroup':
            try:
                id = int(request.POST['id']) if 'id' in request.POST and request.POST['id'] and int(request.POST['id']) != 0 else None
                typeForm = 'edit' if id else 'new'
                f = GrupoPermisoForm(request.POST)
                if not f.is_valid():
                    raise NameError(u"Debe ingresar la información en todos los campos")
                if typeForm == 'new':
                    puede_realizar_accion(request, 'bd.puede_agregar_grupo')
                    if Group.objects.filter(name=f.cleaned_data['name']).exists():
                        raise NameError(u"Nombre debe ser único")
                    grupo = Group(name=f.cleaned_data['name'])
                    grupo.save()
                    #log(u'Aciciono grupo: %s' % grupo, request, "add")
                    if 'permissions' in request.POST:
                        permissions = json.loads(request.POST['permissions'])
                        for permiso in permissions:
                            grupo.permissions.add(permiso)
                            #log(u'Aciciono permisos a grupo: %s' % permiso, request, "add")
                else:
                    puede_realizar_accion(request, 'bd.puede_modificar_grupo')
                    if not Group.objects.filter(pk=id).exists():
                        raise NameError(u"No existe formulario a editar")
                    if Group.objects.filter(name=f.cleaned_data['name']).exclude(pk=id).exists():
                        raise NameError(u"Nombre debe ser único")
                    grupo = Group.objects.filter(pk=id).update(name=f.cleaned_data['name'])

                    #log(u'Edito grupo: %s' % grupo, request, "edit")
                    eGroup = Group.objects.get(pk=id)
                    if 'permissions' in request.POST:
                        permissions = json.loads(request.POST['permissions'])
                        permissions_aux = eGroup.permissions.all()
                        for p in permissions_aux:
                            if not p.id in permissions:
                                eGroup.permissions.remove(p)
                                p.save()
                        for p in Permission.objects.filter(pk__in=permissions):
                            eGroup.permissions.add(p)


                return JsonResponse({"result": "ok", "mensaje": u"Se guardo correctamente el grupo"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar el grupo. %s" % ex.__str__()})

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        if 'action' in request.GET:
            action = request.GET['action']
            # MODULOS
            if action == 'addmodulo':
                try:
                    data['title'] = u'Adicionar Módulo'
                    data['form'] = ModuloForm()
                    data['action'] = action
                    template = get_template("adm_modulo/add.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

            elif action == 'editmodulo':
                try:
                    data['id'] = request.GET['id']
                    data['filtro'] = filtro = Modulo.objects.get(pk=request.GET['id'])
                    data['form'] = ModuloForm(initial=model_to_dict(filtro))
                    data['action'] = action
                    template = get_template("adm_modulo/add.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

            elif action == 'categorias':
                data['title'] = u'Categorias Modulos'
                data['listado'] = CategoriaModulo.objects.filter(status=True).order_by('orden')
                return render(request, "adm_modulo/viewcategorias.html", data)

            elif action == 'addcategoria':
                try:
                    data['title'] = u'Adicionar Módulo'
                    data['form'] = ModuloCategoriaForm()
                    data['action'] = action
                    template = get_template("adm_modulo/formcategoria.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

            elif action == 'editcategoria':
                try:
                    data['id'] = request.GET['id']
                    data['filtro'] = filtro = CategoriaModulo.objects.get(pk=request.GET['id'])
                    data['form'] = ModuloCategoriaForm(initial=model_to_dict(filtro))
                    data['action'] = action
                    template = get_template("adm_modulo/formcategoria.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

            # GRUPO MODULOS

            elif action == 'grupomodulos':
                data['title'] = u'Grupo de Módulos del Sistema'
                return render(request, "adm_modulo/grupo_modulo_view.html", data)

            elif action == 'loadForm':
                try:
                    typeForm = request.GET['typeForm'] if 'typeForm' in request.GET and request.GET['typeForm'] and str(request.GET['typeForm']) in ['new', 'edit', 'view'] else None
                    if typeForm is None:
                        raise NameError(u"No se encontro el tipo de formulario")
                    f = ModuloGrupoForm()
                    eModuloGrupo = None
                    id = 0
                    if typeForm in ['edit', 'view']:
                        id = int(request.GET['id']) if 'id' in request.GET and request.GET['id'] and int(request.GET['id']) != 0 else None
                        if not Modulo.objects.filter(pk=id).exists():
                            raise NameError(u"No existe formulario a editar")
                        eModuloGrupo = ModuloGrupo.objects.get(pk=id)
                        f.initial = model_to_dict(eModuloGrupo)
                        if typeForm == 'view':
                            f.view()
                        if typeForm == 'edit':
                            puede_realizar_accion(request, 'bd.puede_modificar_grupos_modulos')
                        data['eModuloGrupo'] = eModuloGrupo
                    else:
                        puede_realizar_accion(request, 'bd.puede_agregar_grupos_modulos')
                    data['form'] = f
                    data['frmName'] = "frmModuloGrupo"
                    data['id'] = id
                    template = get_template("adm_modulo/frm.html")
                    json_content = template.render(data)
                    return JsonResponse({"result": "ok", 'html': json_content})
                except Exception as ex:
                    return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos. %s" % ex.__str__()})

            elif action == 'grupos':
                try:
                    data['title'] = u'Administración de Grupos del Sistema'
                    return render(request, "adm_modulo/grupos.html", data)
                except Exception as ex:
                    pass

            elif action == 'loadFormGroup':
                try:
                    typeForm = request.GET['typeForm'] if 'typeForm' in request.GET and request.GET['typeForm'] and str(request.GET['typeForm']) in ['new', 'edit', 'view'] else None
                    if typeForm is None:
                        raise NameError(u"No se encontro el tipo de formulario")
                    f = GrupoPermisoForm()
                    eGrupo = None
                    id = 0
                    if typeForm in ['edit', 'view']:
                        id = int(request.GET['id']) if 'id' in request.GET and request.GET['id'] and int(request.GET['id']) != 0 else None
                        if not Group.objects.filter(pk=id).exists():
                            raise NameError(u"No existe formulario a editar")
                        eGrupo = Group.objects.get(pk=id)
                        f.initial = model_to_dict(eGrupo)
                        if typeForm == 'view':
                            f.view()
                        if typeForm == 'edit':
                            puede_realizar_accion(request, 'bd.puede_modificar_grupo')
                        data['ePermissions'] = eGrupo.permissions.all()
                        data['eGrupo'] = eGrupo
                    else:
                        puede_realizar_accion(request, 'bd.puede_agregar_grupo')
                    data['form'] = f
                    data['frmName'] = "frmGrupo"
                    data['typeForm'] = typeForm
                    data['id'] = id
                    template = get_template("adm_modulo/modal/frm.html")
                    json_content = template.render(data)
                    return JsonResponse({"result": "ok", 'html': json_content})
                except Exception as ex:
                    return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos. %s" % ex.__str__()})

            elif action == 'loadPermissions':
                try:
                    if 'permissions' in request.GET:
                        permissions = json.loads(request.GET['permissions'])
                        data['permissions'] = Permission.objects.filter().exclude(pk__in=permissions)
                    else:
                        data['permissions'] = Permission.objects.filter()
                    template = get_template("adm_modulo/modal/permissions.html")
                    json_content = template.render(data)
                    return JsonResponse({"result": "ok", 'html': json_content})
                except Exception as ex:
                    return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos. %s" % ex.__str__()})


            return HttpResponseRedirect(request.path)

        else:
            data['title'] = u'Módulos del Sistema'
            search = None
            ids = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                modulos = Modulo.objects.filter(nombre__icontains=search).filter(status=True).order_by('-id')
            else:
                modulos = Modulo.objects.filter(status=True).order_by('-id', 'activo')
            paging = MiPaginador(modulos, 20)
            p = 1
            try:
                paginasesion = 1
                if 'paginador' in request.session:
                    paginasesion = int(request.session['paginador'])
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                else:
                    p = paginasesion
                try:
                    page = paging.page(p)
                except:
                    p = 1
                page = paging.page(p)
            except:
                page = paging.page(p)
            request.session['paginador'] = p
            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['search'] = search if search else ""
            data['ids'] = ids if ids else ""
            data['modulos'] = page.object_list
            return render(request, "adm_modulo/view.html", data)
