from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login,logout,authenticate
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal,InvalidOperation
from django.db import transaction
from django.utils import timezone
from django.db.models import Prefetch
from .forms import FormularioLogin,UsuarioForm,ProductoForm,CategoriaForm
from .models import Producto,Venta,Usuario,Categoria,Pedido,PedidoProductos,Proveedor,Administrador,EntradaProducto
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.conf import settings
import random # Para generar el número random
from django.http import JsonResponse


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
        return redirect('login')  # Redirige si no hay sesión activa

    cedula_usuario = request.session['user_id']

    try:
        usuario = Usuario.objects.get(cedula=cedula_usuario)
    except Usuario.DoesNotExist:
        return redirect('login')

    # Prefetch los productos de cada pedido
    pedidos = Pedido.objects.filter(cedula=usuario).order_by('-fecha_Creacion')\
        .prefetch_related(
            Prefetch(
                'productos',
                    queryset=PedidoProductos.objects.select_related('id_producto')
                )
            )


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

    context = {
        'categorias': categorias,
        'productos': productos,
        'categoria_seleccionada': categoria_seleccionada, # Para marcar el botón activo si lo deseas
        # El nombre del usuario de la sesión ya está disponible en el request para el header
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
    user_id = request.session.get('user_id')  # ID del usuario en sesión

    if not carrito:
        return render(request, 'usuario/carrito.html', {'error': 'El carrito está vacío.'})

    if not user_id:
        return redirect('login')  # O muestra un mensaje de "inicia sesión"

    usuario = get_object_or_404(Usuario, pk=user_id)

    total = sum(Decimal(item['precio']) * item['cantidad'] for item in carrito.values())

    # Crear el pedido
    pedido = Pedido.objects.create(
        fecha_Creacion=timezone.now(),
        estado_pedido='Pendiente',
        total_pedido=total,
        cedula=usuario
    )

    for id_producto, item in carrito.items():
        producto = get_object_or_404(Producto, pk=id_producto)
        cantidad = item['cantidad']

        # Crear relación PedidoProductos
        PedidoProductos.objects.create(
            id_pedido=pedido,
            id_producto=producto,
            cantidad=cantidad
        )

        # Descontar del stock
        if producto.cantidad_producto < cantidad:
            return render(request, 'usuario/carrito.html', {'error': f"No hay suficiente stock de {producto.descripcion_producto}."})

        producto.cantidad_producto -= cantidad
        producto.save()

        # Actualizar o crear Venta
        venta, created = Venta.objects.get_or_create(producto=producto)
        venta.cantidad_vendida += cantidad
        venta.save()

    # Vaciar carrito
    request.session['carrito'] = {}

    return render(request, 'usuario/compra_exitosa.html', {'pedido': pedido})
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
    return render(request, 'admin/admin.html')
def admin_view2(request):
    return render(request, 'admin/admin_2.html')
def admin_view3(request):
    return render(request, 'admin/admin_3.html')

def admin_usuarios_view(request):
    usuarios = Usuario.objects.all()
    return render(request, 'admin/admin_usuarios.html', {'usuarios': usuarios})

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
    return render(request, 'admin/admin_usuario_form.html', {'form': form, 'title': 'Crear Usuario'})

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
    return render(request, 'admin/admin_usuario_form.html', {'form': form, 'title': f'Editar Usuario: {usuario.nombre}'})

def usuario_delete(request, cedula):
    """
    Permite eliminar un usuario.
    """
    usuario = get_object_or_404(Usuario, cedula=cedula)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('admin_usuarios')
    return render(request, 'admin/admin_usuario_confirm_delete.html', {'usuario': usuario})



def admin_productos_view(request):
    productos = Producto.objects.all()
    return render(request, 'admin/admin_productos.html', {'productos': productos})

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
    return render(request, 'admin/admin_producto_form.html', {'form': form, 'title': 'Crear Producto'})

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
    return render(request, 'admin/admin_producto_form.html', {'form': form, 'title': f'Editar Producto: {producto.descripcion_producto}'})

def producto_delete(request, id_producto): # Usamos 'pk'
    """
    Permite eliminar un producto.
    """
    producto = get_object_or_404(Producto, id_producto=id_producto)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect('admin_productos')
    return render(request, 'admin/admin_producto_confirm_delete.html', {'producto': producto})

def admin_categorias_view(request):
    categorias = Categoria.objects.all()
    return render(request, 'admin/admin_categorias.html', {'categorias': categorias})

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
        return render(request, 'admin/admin_categoria_form.html', {'form': form, 'title': 'Crear Categoría'}) # O 'categorias/categoria_form.html'

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
    return render(request, 'admin/admin_categoria_form.html', {'form': form, 'title': f'Editar Categoría: {categoria.nombre_categoria}'}) # O 'categorias/categoria_form.html'

def categoria_delete(request, id_categoria): # Usamos 'pk'
    """
    Permite eliminar una categoría.
    """
    categoria = get_object_or_404(Categoria, id_categoria=id_categoria)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente.')
        return redirect('admin_categorias')
    return render(request, 'admin/admin_categoria_confirm_delete.html', {'categoria': categoria}) # O 'categorias/categoria_confirm_delete.html'


def admin_pedidos_view(request):
    return render(request, 'admin/admin_pedidos.html')



def admin_proveedores_view(request):
    return render(request, 'admin/admin_proveedores.html')

def admin_entradas_view(request):
    return render(request, 'admin/admin_entradas.html')

def admin_salidas_view(request):
    return render(request, 'admin/admin_salidas.html')

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