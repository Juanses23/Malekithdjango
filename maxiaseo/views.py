from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login,logout,authenticate
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal,InvalidOperation
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from django.db.models import Prefetch
from django.forms import modelformset_factory
from django.utils.dateparse import parse_date

from .forms import FormularioLogin,UsuarioForm,ProductoForm,CategoriaForm,PedidoForm,ProveedorForm,EntradaProductoForm,PedidoUpdateForm,EntradaProductoDetalleForm
from .models import Producto,Venta,Usuario,Categoria,Pedido,PedidoProductos,Proveedor,Administrador,EntradaProducto,EntradaProductoDetalle,HistorialEstadoPedido,Estado
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.conf import settings
import random # Para generar el número random
from django.http import JsonResponse
import json

# Create your views here.
def inicio(request):
    """Vista para la página de inicio"""
    return render(request, 'index.html')

def nuestra_empresa(request):
    """Vista para la página de acerca de"""
    return render(request, 'nuestraEmpresa.html')
from django.shortcuts import render, redirect
from .models import Usuario

def perfil(request):
    cedula = request.session.get("user_id")  # o el campo correspondiente
    usuario = Usuario.objects.get(cedula=cedula)

    if request.method == "POST":
        if 'guardar_nombre' in request.POST:
            usuario.nombre = request.POST['nombre']
        elif 'guardar_apellido' in request.POST:
            usuario.apellido = request.POST['apellido']
        elif 'guardar_telefono' in request.POST:
            usuario.telefono = request.POST['telefono']
        elif 'guardar_direccion' in request.POST:
            usuario.direccion = request.POST['direccion']
        elif 'guardar_ciudad' in request.POST:
            usuario.ciudad = request.POST['ciudad']
        usuario.save()
        return redirect('perfil')

    return render(request, 'usuario/perfil.html', {'usuario': usuario})

def pedidos(request):
    if 'user_id' not in request.session:
        return redirect('login')

    cedula_usuario = request.session['user_id']

    try:
        usuario = Usuario.objects.get(cedula=cedula_usuario)
    except Usuario.DoesNotExist:
        return redirect('login')

    pedidos = Pedido.objects.filter(cedula=usuario).prefetch_related(
        Prefetch('productos', queryset=PedidoProductos.objects.select_related('id_producto')),
        Prefetch('historial_estados', queryset=HistorialEstadoPedido.objects.select_related('estado').order_by('-fecha_cambio'))
    ).order_by('-fecha_Creacion')

    return render(request, 'usuario/pedidos.html', {'pedidos': pedidos})
def login_view(request):
    error_message = None
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password') # Contraseña en texto plano, recuerda la nota de seguridad.

        try:
            # Intenta encontrar un usuario con el email proporcionado
            user = Usuario.objects.get(email=email)
            
            # Verifica si la contraseña coincide.
            # En un sistema real, compararías el hash de la contraseña proporcionada con el hash almacenado.
            if user.password == password: 
                request.session['user_name'] = user.nombre
                request.session['user_id'] = user.cedula # Usamos cedula como ID si es tu primary_key

                if user.id_administrador: 
                    messages.success(request, f'¡Bienvenido administrador, {user.nombre}!')
                    return redirect(reverse('admin_view')) # Redirige a la vista de administrador
                else:
                    messages.success(request, f'¡Bienvenido de nuevo, {user.nombre}!')
                    return redirect(reverse('productos')) # Redirige a la página normal de inicio
                # --- Fin de la lógica de redirección ---
            else:
                error_message = "Correo o contraseña incorrectos."
        except Usuario.DoesNotExist:
            error_message = "Correo o contraseña incorrectos."
        except Exception as e:
            # Captura cualquier otro error, como problemas de base de datos
            error_message = f"Ocurrió un error: {e}"
            
    return render(request, 'login.html', {'error_message': error_message})

def registro_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        cedula = request.POST.get('cedula')
        ciudad = request.POST.get('ciudad')
        email = request.POST.get('email')
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')
        password = request.POST.get('password')
        reppassword = request.POST.get('reppassword')

        # 1. Validación de contraseñas
        if password != reppassword:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'registro.html')
        
        # 2. Validación de correo único
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return render(request, 'registro.html')

        # 3. Validación de cédula única
        if Usuario.objects.filter(cedula=cedula).exists():
            messages.error(request, 'El número de cédula ya está registrado.')
            return render(request, 'registro.html')

        try:
            # Crea una nueva instancia del modelo Usuario
            # ¡ADVERTENCIA DE SEGURIDAD!: Almacenar contraseñas en texto plano es INSEGURO.
            # Usa el hashing de contraseñas si no estás usando el sistema de autenticación de Django.
            
            usuario_nuevo = Usuario.objects.create(
                nombre=nombre,
                apellido=apellido,
                fecha_nacimiento=fecha_nacimiento,
                cedula=cedula,
                ciudad=ciudad,
                email=email,
                direccion=direccion,
                telefono=telefono,
                password=password, # Asume que el password se guarda tal cual en este ejemplo (NO RECOMENDADO)
                # id_administrador=None, # O asigna un objeto Administrador si es necesario
            )
            
            # --- Aquí es donde agregarás el envío de correo ---
            subject = f'¡Bienvenido a maxiaseo, {nombre}!'
            message = (
                f'Hola {nombre} {apellido},\n\n'
                '¡Gracias por registrarte en maxiaseo!\n'
                'Estamos emocionados de tenerte con nosotros.\n\n'
                'Puedes iniciar sesión con tu correo electrónico y la contraseña que creaste.\n\n'
                'Si tienes alguna pregunta, no dudes en contactarnos.\n\n'
                'Saludos,\n'
                'El equipo de maxiaseo'
            )
            from_email = settings.EMAIL_HOST_USER # El correo desde donde se envía (configurado en settings.py)
            recipient_list = [email] # La dirección de correo del nuevo usuario

            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            # --- Fin del envío de correo ---

            messages.success(request, '¡Tu cuenta ha sido creada con éxito y hemos enviado un correo de bienvenida! Ahora puedes iniciar sesión.')
            return redirect(reverse('login'))

        except Exception as e:
            messages.error(request, f'Ocurrió un error al crear la cuenta o enviar el correo: {e}')
            return render(request, 'registro.html')

    return render(request, 'registro.html')


def olvido_contrasena_view(request):
    return render(request, 'olvido_contrasena.html') 


def productos_view(request):
    # Obtener todas las categorías para los botones de filtro
    categorias = Categoria.objects.all()

    # Obtener la categoría seleccionada de los parámetros de la URL (GET)
    categoria_id_str = request.GET.get('categoria', '0') # '0' si no se selecciona ninguna
    
    # Inicializar la categoría seleccionada a 0 (todas)
    categoria_seleccionada = 0
    try:
        categoria_seleccionada = int(categoria_id_str)
    except (ValueError, TypeError):
        # Si el valor no es un número, por seguridad, tratamos como 'todas'
        categoria_seleccionada = 0

    # Obtener los productos
    if categoria_seleccionada > 0:
        # Filtrar productos por la categoría seleccionada
        productos = Producto.objects.filter(id_categoria=categoria_seleccionada)
    else:
        # Mostrar todos los productos
        productos = Producto.objects.all()
    carrito = request.session.get('carrito', {})
    total_items_carrito = sum(item['cantidad'] for item in carrito.values())
    context = {
        'categorias': categorias,
        'productos': productos,
        'categoria_seleccionada': categoria_seleccionada, # Para marcar el botón activo si lo deseas
        'total_items_carrito': total_items_carrito,
    }
    return render(request, 'productos.html', context)

from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect

def carrito_view(request):
    carrito = request.session.get('carrito', {})

    if request.method == 'POST':
        id_producto = str(request.POST.get('id_producto'))
        nombre = request.POST.get('nombre')
        precio_str = request.POST.get('precio', '0').replace(',', '.')
        print("Precio recibido:", precio_str)
        try:
            precio = Decimal(precio_str)
        except (InvalidOperation, TypeError):
            precio = Decimal('0.00')
        cantidad = int(request.POST.get('cantidad'))

        if id_producto in carrito:
            carrito[id_producto]['cantidad'] += cantidad
        else:
            carrito[id_producto] = {
                'nombre': nombre,
                'precio': float(precio),
                'cantidad': cantidad
            }
        request.session['carrito'] = carrito
        return redirect('carrito_view')

    # Calcular subtotales y total
    total = 0
    for item in carrito.values():
        item['subtotal'] = item['precio'] * item['cantidad']
        total += item['subtotal']

    return render(request, 'usuario/carrito.html', {'carrito': carrito, 'total': total})

def vaciar_carrito(request):
    request.session['carrito'] = {}
    return JsonResponse({'ok': True})

def eliminar_item_carrito(request, id_producto):
    carrito = request.session.get('carrito', {})
    if id_producto in carrito:
        del carrito[id_producto]
        request.session['carrito'] = carrito
    return JsonResponse({'ok': True})

def actualizar_cantidad(request):
    if request.method == 'POST':
        id_producto = request.POST.get('id_producto')
        nueva_cantidad = int(request.POST.get('cantidad', 1))
        carrito = request.session.get('carrito', {})

        if id_producto in carrito:
            carrito[id_producto]['cantidad'] = nueva_cantidad
            request.session['carrito'] = carrito
            return JsonResponse({'ok': True})
    return JsonResponse({'ok': False})

@transaction.atomic
def realizar_compra(request):
    carrito = request.session.get('carrito', {})
    metodo = request.session.get('metodo_pago', 'efectivo')
    user_id = request.session.get('user_id')

    if not carrito:
        return render(request, 'usuario/carrito.html', {'error': 'El carrito está vacío.'})
    
    if not user_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, pk=user_id)
    total = sum(Decimal(item['precio']) * item['cantidad'] for item in carrito.values())

    estado_pendiente = get_object_or_404(Estado, nombre='Pendiente')

    pedido = Pedido.objects.create(
        fecha_Creacion=timezone.now(),
        estado_pedido=estado_pendiente,
        total_pedido=total,
        cedula=usuario,
        metodo=metodo
    )

    for id_producto, item in carrito.items():
        producto = get_object_or_404(Producto, pk=id_producto)
        cantidad = item['cantidad']

        if producto.cantidad_producto < cantidad:
            return render(request, 'usuario/carrito.html', {
                'error': f"No hay suficiente stock de {producto.descripcion_producto}."
            })

        PedidoProductos.objects.create(
            id_pedido=pedido,
            id_producto=producto,
            cantidad=cantidad
        )

        producto.cantidad_producto -= cantidad
        producto.save()

        venta, _ = Venta.objects.get_or_create(producto=producto)
        venta.cantidad_vendida += cantidad
        venta.save()

    request.session['carrito'] = {}
    request.session['metodo_pago'] = None

    return render(request, 'usuario/compra_exitosa.html', {'pedido': pedido})


def seleccionar_metodo_pago(request):
    if request.method == 'POST':
        metodo = request.POST.get('metodo')
        request.session['metodo_pago'] = metodo
        return redirect('realizar_compra')

    return render(request, 'usuario/metodo_pago.html')

def logout_view(request):
    # Eliminar las variables de sesión del usuario
    if 'user_name' in request.session:
        del request.session['user_name']
    if 'user_id' in request.session:
        del request.session['user_id']
    
    # También puedes llamar a request.session.flush() para eliminar todos los datos de la sesión
    # request.session.flush()

    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect(reverse('inicio')) # Redirige al login o a la página de inicio



def olvido_contrasena_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            # 1. Verificar si el correo existe en la base de datos
            usuario = Usuario.objects.get(email=email)
            
            # 2. Generar código de verificación aleatorio (6 dígitos)
            codigo_verificacion = random.randint(100000, 999999)

            # 3. Guardar el código y el email del usuario en la sesión de Django
            # La sesión de Django es el equivalente a 'session.setAttribute' en JSP
            request.session['codigo_recuperacion'] = codigo_verificacion
            request.session['email_recuperacion'] = email # Guardamos el email para la siguiente vista

            # 4. Enviar el correo con el código
            subject = 'Código de Recuperación de Contraseña'
            message = (
                f'Hola {usuario.nombre},\n\n'
                f'Tu código de recuperación de contraseña es: {codigo_verificacion}\n\n'
                'Por favor, ingresa este código en la siguiente pantalla para restablecer tu contraseña.\n'
                'Si no solicitaste esto, puedes ignorar este correo.\n\n'
                'Saludos,\n'
                'El equipo de [Nombre de tu Empresa/Servicio]'
            )
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]

            send_mail(subject, message, from_email, recipient_list, fail_silently=False)

            # 5. Redirigir a la próxima vista (donde el usuario ingresará el código)
            messages.success(request, 'Se ha enviado un código de verificación a tu correo electrónico.')
            return redirect(reverse('verificar_codigo_recuperacion')) # Necesitas definir esta URL

        except Usuario.DoesNotExist:
            # Si el correo no está registrado
            messages.error(request, 'Correo no registrado. Por favor, verifica el correo e inténtalo de nuevo.')
            return render(request, 'olvido_contrasena.html', {'email': email}) # Mantener el email en el campo
        except Exception as e:
            # Manejar cualquier otro error (problemas de conexión, envío de correo, etc.)
            messages.error(request, f'Ocurrió un error al procesar tu solicitud: {e}')
            return render(request, 'olvido_contrasena.html', {'email': email})

    # Si la solicitud es GET, simplemente muestra el formulario vacío
    return render(request, 'olvido_contrasena.html')


# --- Nueva vista para verificar el código ---
def verificar_codigo_recuperacion_view(request):
    # Obtener el código y el email de la sesión
    codigo_esperado = request.session.get('codigo_recuperacion')
    email_recuperacion = request.session.get('email_recuperacion')

    if not codigo_esperado or not email_recuperacion:
        messages.error(request, 'No hay una solicitud de recuperación de contraseña activa o la sesión ha expirado.')
        return redirect(reverse('olvido_contrasena')) # Redirigir a la página de olvido si no hay sesión

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')

        if str(codigo_ingresado) == str(codigo_esperado):
            # Código correcto, redirigir a la página para restablecer la contraseña
            messages.success(request, 'Código verificado correctamente. Ahora puedes restablecer tu contraseña.')
            return redirect(reverse('restablecer_contrasena')) # Necesitas definir esta URL
        else:
            messages.error(request, 'Código incorrecto. Inténtalo de nuevo.')
            # Renderiza la plantilla nuevamente con el mensaje de error
            return render(request, 'cod_recuperar_contra.html')
    
    # Si la solicitud es GET, simplemente muestra el formulario para ingresar el código
    return render(request, 'cod_recuperar_contra.html')


# --- Nueva vista para restablecer la contraseña (ejemplo) ---
def restablecer_contrasena_view(request):
    email_recuperacion = request.session.get('email_recuperacion')

    if not email_recuperacion:
        messages.error(request, 'No hay una solicitud de restablecimiento de contraseña activa.')
        return redirect(reverse('olvido_contrasena'))

    if request.method == 'POST':
        nueva_password = request.POST.get('nueva_password')
        confirmar_password = request.POST.get('confirmar_password')

        if nueva_password != confirmar_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'restablecer_contrasena.html', {'email': email_recuperacion})

        try:
            usuario = Usuario.objects.get(email=email_recuperacion)
            # Aquí es donde ACTUALIZARÍAS la contraseña.
            # ¡IMPORTANTE!: NUNCA guardes la contraseña en texto plano.
            # Usa una función de hashing como `make_password` de Django.
            # from django.contrib.auth.hashers import make_password
            # usuario.password = make_password(nueva_password)
            usuario.password = nueva_password # ¡ADVERTENCIA: INSEGURO para demostración!
            usuario.save()

            # Opcional: Limpiar la sesión después de restablecer la contraseña
            if 'codigo_recuperacion' in request.session:
                del request.session['codigo_recuperacion']
            if 'email_recuperacion' in request.session:
                del request.session['email_recuperacion']

            messages.success(request, '¡Tu contraseña ha sido restablecida con éxito! Ya puedes iniciar sesión.')
            return redirect(reverse('login'))

        except Usuario.DoesNotExist:
            messages.error(request, 'El usuario asociado a la recuperación no fue encontrado.')
            return redirect(reverse('olvido_contrasena'))
        except Exception as e:
            messages.error(request, f'Ocurrió un error al restablecer la contraseña: {e}')
            return render(request, 'restablecer_contrasena.html', {'email': email_recuperacion})

    return render(request, 'restablecer_contrasena.html', {'email': email_recuperacion})

def admin_view(request):
    productos_bajo_stock = Producto.objects.filter(cantidad_producto__lt=10)
    return render(request, 'admin/admin.html', {
        'productos_bajo_stock': productos_bajo_stock,
        'total_bajo_stock': productos_bajo_stock.count()
    })

def admin_view2(request):
    productos_bajo_stock = Producto.objects.filter(cantidad_producto__lt=10)

    return render(request, 'admin/admin_2.html', {
        'productos_bajo_stock': productos_bajo_stock,
        'total_bajo_stock': productos_bajo_stock.count()
    })

def panel_admin(request):
    top_n = request.GET.get('top_n', '10')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Filtro por fecha
    ventas = Venta.objects.all()
    if fecha_inicio:
        ventas = ventas.filter(fecha_venta__gte=parse_date(fecha_inicio))
    if fecha_fin:
        ventas = ventas.filter(fecha_venta__lte=parse_date(fecha_fin))

    # Datos para gráfico de pastel (productos vendidos)
    ventas_por_producto = (
        ventas.values('producto__descripcion_producto')
        .annotate(total_vendido=Sum('cantidad_vendida'))
        .order_by('-total_vendido')
    )
    if top_n != 'all':
        ventas_por_producto = ventas_por_producto[:int(top_n)]

    labels_pastel = [v['producto__descripcion_producto'] for v in ventas_por_producto]
    data_pastel = [v['total_vendido'] for v in ventas_por_producto]

    # Datos para gráfico de líneas (ventas por fecha)
    ventas_por_fecha = (
        ventas.values('fecha_venta')
        .annotate(total_vendido=Sum('cantidad_vendida'))
        .order_by('fecha_venta')
    )
    labels_linea = [v['fecha_venta'].strftime('%Y-%m-%d') for v in ventas_por_fecha]
    data_linea = [v['total_vendido'] for v in ventas_por_fecha]

    context = {
    'labels_pastel': json.dumps(labels_pastel),
    'data_pastel': json.dumps(data_pastel),
    'labels_linea': json.dumps(labels_linea),
    'data_linea': json.dumps(data_linea),
    'top_n': top_n,
    'fecha_inicio': fecha_inicio,
    'fecha_fin': fecha_fin,
    }
    return render(request, 'admin/admin_panel.html', context)
def admin_usuarios_view(request):
    usuarios = Usuario.objects.all()
    return render(request, 'admin/usuario/usuarios.html', {'usuarios': usuarios})

def usuario_create(request):
    """
    Permite crear un nuevo usuario.
    """
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('admin_usuarios')
        else:
            messages.error(request, 'Hubo un error al crear el usuario. Por favor, revisa los datos.')
    else:
        form = UsuarioForm()
    return render(request, 'admin/usuario/usuario_form.html', {'form': form, 'title': 'Crear Usuario'})

def usuario_update(request, cedula):
    """
    Permite editar un usuario existente.
    """
    usuario = get_object_or_404(Usuario, cedula=cedula)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('admin_usuarios')
        else:
            messages.error(request, 'Hubo un error al actualizar el usuario. Por favor, revisa los datos.')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'admin/usuario/usuario_form.html', {'form': form, 'title': f'Editar Usuario: {usuario.nombre}'})

def usuario_delete(request, cedula):
    """
    Permite eliminar un usuario.
    """
    usuario = get_object_or_404(Usuario, cedula=cedula)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('admin_usuarios')
    return render(request, 'admin/usuario/usuario_confirm_delete.html', {'usuario': usuario})



def admin_productos_view(request):
    productos = Producto.objects.all()
    return render(request, 'admin/producto/productos.html', {'productos': productos})

def producto_create(request):
    """
    Permite crear un nuevo producto.
    """
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('admin_productos')
        else:
            messages.error(request, 'Hubo un error al crear el producto. Por favor, revisa los datos.')
    else:
        form = ProductoForm()
    return render(request, 'admin/producto/producto_form.html', {'form': form, 'title': 'Crear Producto'})

def producto_update(request, id_producto): # Usamos 'pk' porque id_producto es AutoField (primary key)
    """
    Permite editar un producto existente.
    """
    producto = get_object_or_404(Producto, id_producto=id_producto)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('admin_productos')
        else:
            messages.error(request, 'Hubo un error al actualizar el producto. Por favor, revisa los datos.')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'admin/producto/producto_form.html', {'form': form, 'title': f'Editar Producto: {producto.descripcion_producto}'})

def producto_delete(request, id_producto): # Usamos 'pk'
    """
    Permite eliminar un producto.
    """
    producto = get_object_or_404(Producto, id_producto=id_producto)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect('admin_productos')
    return render(request, 'admin/producto/producto_confirm_delete.html', {'producto': producto})

def admin_categorias_view(request):
    categorias = Categoria.objects.all()
    return render(request, 'admin/categoria/categorias.html', {'categorias': categorias})

def categoria_create(request):
    """
    Permite crear una nueva categoría.
    """
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('admin_categorias')
        else:
            messages.error(request, 'Hubo un error al crear la categoría. Por favor, revisa los datos.')
    else:
        form = CategoriaForm()
        return render(request, 'admin/categoria/categoria_form.html', {'form': form, 'title': 'Crear Categoría'}) # O 'categorias/categoria_form.html'

def categoria_update(request, id_categoria): # Usamos 'pk' porque id_categoria es AutoField (primary key)
    """
    Permite editar una categoría existente.
    """
    categoria = get_object_or_404(Categoria, id_categoria=id_categoria)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('admin_categorias')
        else:
            messages.error(request, 'Hubo un error al actualizar la categoría. Por favor, revisa los datos.')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'admin/categoria/categoria_form.html', {'form': form, 'title': f'Editar Categoría: {categoria.nombre_categoria}'}) # O 'categorias/categoria_form.html'

def categoria_delete(request, id_categoria): # Usamos 'pk'
    """
    Permite eliminar una categoría.
    """
    categoria = get_object_or_404(Categoria, id_categoria=id_categoria)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente.')
        return redirect('admin_categorias')
    return render(request, 'admin/categoria/categoria_confirm_delete.html', {'categoria': categoria}) # O 'categorias/categoria_confirm_delete.html'


def admin_pedidos_view(request):
    """
    Muestra una lista de todos los pedidos, incluyendo los productos dentro de cada uno.
    """
    # ¡CAMBIO AQUÍ! Usa 'productos' en lugar de 'productos_del_pedido'
    pedidos = Pedido.objects.select_related('cedula').prefetch_related('productos__id_producto').order_by('-fecha_Creacion')
    return render(request, 'admin/pedido/pedidos.html', {'pedidos': pedidos})

def pedido_create(request):
    """
    Permite crear un nuevo pedido. (No cambia su lógica original)
    """
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pedido creado exitosamente.')
            return redirect('admin_pedidos')
        else:
            messages.error(request, 'Hubo un error al crear el pedido. Por favor, revisa los datos.')
    else:
        form = PedidoForm()
    return render(request, 'admin/pedido/pedido_form.html', {'form': form, 'title': 'Crear Pedido'})

def pedido_update(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == 'POST':
        form = PedidoUpdateForm(request.POST, instance=pedido)
        print(request.POST)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['estado_pedido']
            descripcion = form.cleaned_data['descripcion']
            estado_anterior = pedido.estado_pedido

            # Actualiza el pedido
            pedido.estado_pedido = nuevo_estado
            pedido.save()

            # Siempre guarda en historial
            HistorialEstadoPedido.objects.create(
                pedido=pedido,
                estado=nuevo_estado,
                descripcion=descripcion
            )

            messages.success(request, f'Estado actualizado correctamente.')
            return redirect('admin_pedidos')
        else:
            messages.error(request, 'Formulario inválido')
    else:
        form = PedidoUpdateForm(instance=pedido)

    productos_en_pedido_data = []
    for pp in pedido.productos.select_related('id_producto'):
        subtotal = pp.id_producto.valor_producto * pp.cantidad if pp.id_producto.valor_producto and pp.cantidad else None
        productos_en_pedido_data.append({
            'producto': pp.id_producto,
            'cantidad': pp.cantidad,
            'subtotal': subtotal
        })

    historial = pedido.historial_estados.select_related('estado').order_by('-fecha_cambio')

    return render(request, 'admin/pedido/pedido_form.html', {
        'form': form,
        'title': f'Editar Pedido #{pedido.id_pedido}',
        'pedido_obj': pedido,
        'productos_en_pedido': productos_en_pedido_data,
        'historial': historial
    })
def pedido_delete(request, pk):
    """
    Permite eliminar un pedido. (No cambia)
    """
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        pedido.delete()
        messages.success(request, 'Pedido eliminado exitosamente.')
        return redirect('pedido_list')
    return render(request, 'admin/pedido/pedido_confirm_delete.html', {'pedido': pedido})



def admin_proveedores_view(request):
    """
    Muestra una lista de todos los proveedores.
    """
    proveedores = Proveedor.objects.all().order_by('nombre_proveedor')
    return render(request, 'admin/proveedor/proveedores.html', {'proveedores': proveedores})

def proveedor_create(request):
    """
    Permite crear un nuevo proveedor.
    """
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor creado exitosamente.')
            return redirect('admin_proveedores') # Redirige a la lista de proveedores
        else:
            messages.error(request, 'Hubo un error al crear el proveedor. Por favor, revisa los datos.')
    else:
        form = ProveedorForm()
    return render(request, 'admin/proveedor/proveedor_form.html', {'form': form, 'title': 'Crear Proveedor'})

def proveedor_update(request, pk): # Usamos 'pk' porque id_proveedor es AutoField (primary key)
    """
    Permite editar un proveedor existente.
    """
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente.')
            return redirect('admin_proveedores') # Redirige a la lista de proveedores
        else:
            messages.error(request, 'Hubo un error al actualizar el proveedor. Por favor, revisa los datos.')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'admin/proveedor/proveedor_form.html', {'form': form, 'title': f'Editar Proveedor: {proveedor.nombre_proveedor}'})

def proveedor_delete(request, pk): # Usamos 'pk'
    """
    Permite eliminar un proveedor.
    """
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado exitosamente.')
        return redirect('admin_proveedores') # Redirige a la lista de proveedores
    # Nota: Aquí se renderiza el template de confirmación con la ruta corregida
    return render(request, 'admin/proveedor/proveedor_confirm_delete.html', {'proveedor': proveedor})


def admin_entradas_view(request):
    entradas = EntradaProducto.objects.prefetch_related(
        Prefetch('detalles', queryset=EntradaProductoDetalle.objects.select_related('producto'))
    ).order_by('-fecha_entrada', '-id_entrada_producto')

    # Creamos un diccionario con los totales
    totales = {}
    for entrada in entradas:
        total = sum((detalle.costo_total for detalle in entrada.detalles.all()), Decimal('0.00'))
        totales[entrada.id_entrada_producto] = total

    return render(request, 'admin/entrada/entradas.html', {
        'entradas': entradas,
        'totales': totales
    })
def entrada_create(request):
    DetalleFormSet = modelformset_factory(EntradaProductoDetalle, form=EntradaProductoDetalleForm, extra=1)

    if request.method == 'POST':
        entrada_form = EntradaProductoForm(request.POST)
        formset = DetalleFormSet(request.POST, queryset=EntradaProductoDetalle.objects.none())

        if entrada_form.is_valid() and formset.is_valid():
            entrada = entrada_form.save()

            for form in formset:
                if form.cleaned_data:
                    producto = form.cleaned_data['producto']
                    cantidad = form.cleaned_data['cantidad']
                    costo_total = producto.valor_producto * Decimal(cantidad)

                    EntradaProductoDetalle.objects.create(
                        entrada=entrada,
                        producto=producto,
                        cantidad=cantidad,
                        costo_total=costo_total
                    )

                    # Actualizar stock
                    producto.cantidad_producto += cantidad
                    producto.save()

            messages.success(request, 'Entrada registrada con múltiples productos.')
            return redirect('admin_entradas')
        else:
            messages.error(request, 'Hay errores en el formulario.')
    else:
        entrada_form = EntradaProductoForm()
        formset = DetalleFormSet(queryset=EntradaProductoDetalle.objects.none())

    return render(request, 'admin/entrada/entrada_form.html', {
        'entrada_form': entrada_form,
        'formset': formset,
        'title': 'Registrar Entrada de Productos'
    })

def entrada_update(request, pk):
    entrada = get_object_or_404(EntradaProducto, pk=pk)
    # Guardamos la cantidad original para calcular la diferencia
    cantidad_original = entrada.cantidad_producto
    producto_original = entrada.id_producto # También el producto original

    if request.method == 'POST':
        form = EntradaProductoForm(request.POST, instance=entrada)
        if form.is_valid():
            entrada_actualizada = form.save(commit=False)

            # Si el producto asociado ha cambiado, revertir el cambio de cantidad en el producto original
            if producto_original != entrada_actualizada.id_producto:
                producto_original.cantidad_producto -= cantidad_original
                producto_original.save()

            # Obtener el producto actual y la nueva cantidad
            producto_actual = entrada_actualizada.id_producto
            cantidad_nueva = entrada_actualizada.cantidad_producto

            # Recalcular el costo total de la entrada con los nuevos valores
            costo_unitario_producto = producto_actual.valor_producto
            entrada_actualizada.costo_entrada = costo_unitario_producto * Decimal(cantidad_nueva)

            entrada_actualizada.save()

            # Actualizar la cantidad en el producto
            if producto_original == entrada_actualizada.id_producto: # Mismo producto
                diferencia_cantidad = cantidad_nueva - cantidad_original
                producto_actual.cantidad_producto += diferencia_cantidad
            else: # Producto diferente
                producto_actual.cantidad_producto += cantidad_nueva

            producto_actual.save()

            messages.success(request, 'Entrada de producto actualizada exitosamente y cantidad de producto ajustada.')
            return redirect('admin_entradas')
        else:
            messages.error(request, 'Hubo un error al actualizar la entrada. Por favor, revisa los datos.')
    else:
        form = EntradaProductoForm(instance=entrada)
    return render(request, 'admin/entrada/entrada_form.html', {'form': form, 'title': f'Editar Entrada: {entrada.id_entrada_producto}'})


def calcular_costo_entrada_ajax(request):
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        producto_id = request.GET.get('producto_id')
        cantidad = request.GET.get('cantidad')

        # --- Impresiones de Depuración ---
        print(f"DEBUG: AJAX Request received - producto_id: {producto_id}, cantidad: {cantidad}")

        if not producto_id or not cantidad:
            print("DEBUG: Missing producto_id or cantidad. Returning 400.")
            return JsonResponse({'error': 'producto_id y cantidad son requeridos.'}, status=400)

        try:
            producto = Producto.objects.get(pk=producto_id)
            print(f"DEBUG: Found Product: {producto.descripcion_producto} (ID: {producto.id_producto})")
            print(f"DEBUG: Product valor_producto (costo unitario): {producto.valor_producto}")

            cantidad_num = Decimal(cantidad)
            print(f"DEBUG: Converted cantidad to Decimal: {cantidad_num}")

            if cantidad_num <= 0:
                print("DEBUG: Quantity is zero or less. Returning 400.")
                return JsonResponse({'error': 'La cantidad debe ser mayor que cero.'}, status=400)

            costo_unitario = producto.valor_producto

            if costo_unitario is None:
                print("DEBUG: Product valor_producto is None. Returning 400.")
                return JsonResponse({'error': 'El producto seleccionado no tiene un valor de producto definido.'}, status=400)

            # Asegurarse de que costo_unitario también sea Decimal para la multiplicación
            if not isinstance(costo_unitario, Decimal):
                try:
                    costo_unitario = Decimal(str(costo_unitario)) # Convertir a Decimal si no lo es
                    print(f"DEBUG: Converted costo_unitario to Decimal: {costo_unitario}")
                except Exception as e:
                    print(f"ERROR: Could not convert costo_unitario to Decimal: {costo_unitario}, Error: {e}")
                    return JsonResponse({'error': 'Error interno al procesar el costo unitario del producto.'}, status=500)


            costo_total = costo_unitario * cantidad_num
            print(f"DEBUG: Calculated costo_total: {costo_total}")

            return JsonResponse({'costo_total': str(costo_total)})
        except Producto.DoesNotExist:
            print(f"DEBUG: Producto with ID {producto_id} not found. Returning 404.")
            return JsonResponse({'error': 'Producto no encontrado.'}, status=404)
        except (ValueError, TypeError) as e:
            print(f"DEBUG: ValueError or TypeError: {e}. Returning 400.")
            return JsonResponse({'error': f'Cantidad o ID de producto inválidos. Detalle: {e}'}, status=400)
        except Exception as e:
            print(f"DEBUG: Unexpected error: {e}. Returning 500.")
            return JsonResponse({'error': f'Error interno del servidor: {e}'}, status=500)
    print("DEBUG: Request is not GET or not XMLHttpRequest. Returning 400.")
    return JsonResponse({'error': 'Solicitud inválida.'}, status=400)

# ... (tu vista pedido_delete, admin_view, etc.)
def entrada_delete(request, pk): # Usamos 'pk'
    """
    Permite eliminar una entrada de producto.
    """
    entrada = get_object_or_404(EntradaProducto, pk=pk)
    if request.method == 'POST':
        entrada.delete()
        messages.success(request, 'Entrada de producto eliminada exitosamente.')
        return redirect('admin_entradas') # Redirige a la lista de entradas
    return render(request, 'admin/entrada/entrada_confirm_delete.html', {'entrada': entrada})



def admin_ventas_view(request):
    return render(request, 'admin/admin_ventas.html')


def admin_envio_masivo(request):
    if request.method == 'POST':
        tipo_envio = request.POST.get('tipo_envio')
        asunto = request.POST.get('asunto')
        mensaje = request.POST.get('mensaje')

        if tipo_envio == 'todos':
            destinatarios = list(Usuario.objects.values_list('email', flat=True))
        elif tipo_envio == 'uno':
            destinatarios = [request.POST.get('email_destino')]
        else:
            messages.error(request, 'Tipo de envío no válido.')
            return redirect('admin_envio_masivo')

        if not destinatarios:
            messages.warning(request, 'No se encontraron destinatarios.')
            return redirect('admin_envio_masivo')

        try:
            email = EmailMessage(
                asunto,
                mensaje,
                'codenova856@gmail.com',
                bcc=destinatarios if tipo_envio == 'todos' else None,
                to=destinatarios if tipo_envio == 'uno' else None,
            )
            email.send()
            messages.success(request, f'Correo enviado exitosamente {"a todos" if tipo_envio == "todos" else "al usuario seleccionado"}.')
            return redirect('admin_envio_masivo')
        except BadHeaderError:
            messages.error(request, 'Encabezado no válido encontrado.')
        except Exception as e:
            messages.error(request, f'Error al enviar correos: {e}')
    
    usuarios = Usuario.objects.all()
    return render(request, 'admin/admin_envio_masivo.html', {'usuarios': usuarios})