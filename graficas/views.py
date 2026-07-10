import json

import pandas as pd
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .forms import UploadExcelForm
from .models import ConjuntoGraficas, RegistroEnergia

HORA_COLS = [f'Hora: {i}' for i in range(1, 25)]
COLUMNAS_REQUERIDAS = ['FECHA', 'Id de Cliente', 'Tipo de Energía'] + HORA_COLS

# Colores fijos por tipo de energía para que las gráficas sean consistentes
COLORES_TIPO = {
    'Activa': '#2563eb',
    'Reactiva': '#f59e0b',
    'Capacitiva': '#10b981',
    'Penalizada': '#ef4444',
    'Factor': '#8b5cf6',
}


def _normalizar_columnas(df):
    """Limpia espacios y variantes de nombre de columnas del Excel."""
    df.columns = [str(c).strip() for c in df.columns]
    # Aceptar 'Tipo de E...' truncado o variantes de tilde
    for c in df.columns:
        if c.lower().startswith('tipo de e'):
            df = df.rename(columns={c: 'Tipo de Energía'})
    return df


def cargar_archivo(request):
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            nombre = form.cleaned_data['nombre']

            try:
                df = pd.read_excel(archivo)
            except Exception as e:
                messages.error(request, f'No se pudo leer el archivo: {e}')
                return redirect('graficas:cargar')

            df = _normalizar_columnas(df)

            faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
            if faltantes:
                messages.error(
                    request,
                    f'Faltan columnas en el archivo: {", ".join(faltantes)}'
                )
                return redirect('graficas:cargar')

            conjunto = ConjuntoGraficas.objects.create(
                nombre=nombre, archivo_original=archivo.name
            )

            registros = []
            filas_con_error = 0
            for _, fila in df.iterrows():
                try:
                    horas = [
                        float(fila[c]) if pd.notna(fila[c]) else 0.0
                        for c in HORA_COLS
                    ]
                    total = (
                        float(fila['TOTAL'])
                        if 'TOTAL' in df.columns and pd.notna(fila.get('TOTAL'))
                        else sum(horas)
                    )
                    registros.append(RegistroEnergia(
                        conjunto=conjunto,
                        fecha=pd.to_datetime(fila['FECHA']).date(),
                        id_cliente=str(fila['Id de Cliente']),
                        tipo_energia=str(fila['Tipo de Energía']).strip(),
                        horas=horas,
                        total=total,
                    ))
                except Exception:
                    filas_con_error += 1
                    continue

            if not registros:
                conjunto.delete()
                messages.error(request, 'No se pudo procesar ninguna fila del archivo.')
                return redirect('graficas:cargar')

            with transaction.atomic():
                RegistroEnergia.objects.bulk_create(registros)

            msg = f'Se cargaron {len(registros)} registros correctamente.'
            if filas_con_error:
                msg += f' ({filas_con_error} filas se omitieron por errores de formato).'
            messages.success(request, msg)
            return redirect('graficas:detalle', conjunto_id=conjunto.id)
    else:
        form = UploadExcelForm()

    return render(request, 'graficas/upload.html', {'form': form})


def lista_conjuntos(request):
    conjuntos = ConjuntoGraficas.objects.all()
    return render(request, 'graficas/lista.html', {'conjuntos': conjuntos})


def eliminar_conjunto(request, conjunto_id):
    conjunto = get_object_or_404(ConjuntoGraficas, id=conjunto_id)
    if request.method == 'POST':
        nombre = conjunto.nombre
        conjunto.delete()
        messages.success(request, f'Se eliminó el conjunto "{nombre}".')
        return redirect('graficas:lista')
    return render(request, 'graficas/confirmar_eliminar.html', {'conjunto': conjunto})


def detalle_conjunto(request, conjunto_id):
    conjunto = get_object_or_404(ConjuntoGraficas, id=conjunto_id)
    registros = list(conjunto.registros.all())

    tipos = list(dict.fromkeys(r.tipo_energia for r in registros))
    colores = {t: COLORES_TIPO.get(t, '#6b7280') for t in tipos}

    # 1) Hora vs Energía: promedio de cada hora, una serie por tipo
    datos_hora = {t: [0.0] * 24 for t in tipos}
    conteo_hora = {t: [0] * 24 for t in tipos}
    for r in registros:
        for i, v in enumerate(r.horas or []):
            datos_hora[r.tipo_energia][i] += v
            conteo_hora[r.tipo_energia][i] += 1
    for t in tipos:
        datos_hora[t] = [
            round(datos_hora[t][i] / conteo_hora[t][i], 3) if conteo_hora[t][i] else 0
            for i in range(24)
        ]

    # 2) Día vs Energía: suma del total por día, una serie por tipo
    fechas = sorted(set(r.fecha for r in registros))
    datos_dia = {t: [] for t in tipos}
    for t in tipos:
        for f in fechas:
            suma = sum(
                (r.total if r.total is not None else sum(r.horas or []))
                for r in registros if r.tipo_energia == t and r.fecha == f
            )
            datos_dia[t].append(round(suma, 2))

    # 3) Total por tipo de energía (para el diagrama)
    datos_total = {}
    for t in tipos:
        datos_total[t] = round(sum(
            (r.total if r.total is not None else sum(r.horas or []))
            for r in registros if r.tipo_energia == t
        ), 2)

    context = {
        'conjunto': conjunto,
        'tipos': tipos,
        'colores_json': json.dumps(colores),
        'horas_labels_json': json.dumps([f'{i}h' for i in range(1, 25)]),
        'datos_hora_json': json.dumps(datos_hora),
        'dias_labels_json': json.dumps([f.strftime('%Y-%m-%d') for f in fechas]),
        'datos_dia_json': json.dumps(datos_dia),
        'datos_total_json': json.dumps(datos_total),
    }
    return render(request, 'graficas/detalle.html', context)
