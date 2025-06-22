from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario,Producto,Categoria,Pedido,Proveedor,EntradaProducto,PedidoProductos,EntradaProductoDetalle,Estado
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

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = [
            'estado_pedido', 'total_pedido', 'cedula'
        ]
        # Opcional: Widgets para estado_pedido si tienes opciones fijas
        # widgets = {
        #     'estado_pedido': forms.Select(choices=[
        #         ('Pendiente', 'Pendiente'),
        #         ('Procesando', 'Procesando'),
        #         ('Enviado', 'Enviado'),
        #         ('Entregado', 'Entregado'),
        #         ('Cancelado', 'Cancelado'),
        #     ])
        # }

# NUEVO FORMULARIO: PedidoUpdateForm para editar solo el estado
class PedidoUpdateForm(forms.ModelForm):
    estado_pedido = forms.ModelChoiceField(
        queryset=Estado.objects.all(),
        widget=forms.Select(attrs={'class': 'estado-select'}),
        label='Estado'
    )
    descripcion = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Motivo del cambio'}),
        label='Descripción del cambio'
    )

    class Meta:
        model = Pedido
        fields = ['estado_pedido']

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            'nombre_proveedor', 'email', 'razon_social', 'nit', 'telefono'
        ]
class EntradaProductoForm(forms.ModelForm):
    class Meta:
        model = EntradaProducto
        fields = ['descripcion', 'fecha_entrada', 'id_proveedor']
        widgets = {
            'fecha_entrada': forms.DateInput(attrs={'type': 'date'}),
        }
        
class EntradaProductoDetalleForm(forms.ModelForm):
    class Meta:
        model = EntradaProductoDetalle
        fields = ['producto', 'cantidad']
