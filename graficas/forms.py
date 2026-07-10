from django import forms


class UploadExcelForm(forms.Form):
    nombre = forms.CharField(
        max_length=200,
        label='Nombre del conjunto de gráficas',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Cliente 1082527 - Junio 2026'
        }),
    )
    archivo = forms.FileField(
        label='Archivo Excel (.xlsx)',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            raise forms.ValidationError('El archivo debe ser un Excel (.xlsx o .xls).')
        if archivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('El archivo no debe superar 10 MB.')
        return archivo
