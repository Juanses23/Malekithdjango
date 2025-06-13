from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario,Producto,Categoria
class FormularioLogin(AuthenticationForm):
    pass

class UsuarioForm(forms.ModelForm):
    # Opcional: Si quieres un campo de fecha más amigable, puedes usar un DateInput
    # fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Usuario
        fields = [
            'nombre', 'apellido', 'fecha_nacimiento', 'cedula',
            'ciudad', 'email', 'direccion', 'telefono', 'password',
            'id_administrador'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'password': forms.PasswordInput(), # Para ocultar la contraseña
        }
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'descripcion_producto', 'cantidad_producto', 'valor_producto',
            'imagen', 'id_categoria'
        ]
        # Puedes añadir widgets personalizados si necesitas un control específico,
        # por ejemplo, para la imagen si fueras a manejar FileField.
        # En este caso, como es CharField para la imagen, un campo de texto simple está bien.
class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre_categoria']
