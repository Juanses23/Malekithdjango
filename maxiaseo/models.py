from django.db import models
from django.utils import timezone

class Administrador(models.Model):
    id_administrador = models.AutoField(primary_key=True)

    def __str__(self):
        return str(self.id_administrador)

class Usuario(models.Model):
    nombre = models.CharField(max_length=30)
    apellido = models.CharField(max_length=30)
    fecha_nacimiento = models.DateField()
    cedula = models.CharField(max_length=10, primary_key=True)
    ciudad = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=50, unique=True)
    direccion = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=30)
    id_administrador = models.ForeignKey(Administrador, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre_categoria = models.CharField(max_length=100)
    class Meta:
        db_table = 'Categoria'
    def __str__(self):
        return self.nombre_categoria

class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    descripcion_producto = models.CharField(max_length=100)
    cantidad_producto = models.PositiveIntegerField()
    valor_producto = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.CharField(max_length=100, blank=True, null=True)
    id_categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    class Meta:
        db_table = 'Producto'
    def __str__(self):
        return self.descripcion_producto

class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre_proveedor = models.CharField(max_length=30)
    email = models.EmailField(max_length=30, blank=True, null=True)
    razon_social = models.CharField(max_length=50, blank=True, null=True)
    nit = models.FloatField(blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.nombre_proveedor

class EntradaProducto(models.Model):
    id_entrada_producto = models.AutoField(primary_key=True)
    nombre_producto = models.CharField(max_length=100)
    fecha_entrada = models.DateField()
    cantidad_producto = models.IntegerField()
    costo_entrada = models.IntegerField()
    id_proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, blank=True, null=True)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre_producto

class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    fecha_Creacion = models.DateTimeField(auto_now_add=True)
    estado_pedido = models.CharField(max_length=30)
    total_pedido = models.DecimalField(max_digits=20, decimal_places=2)
    cedula = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id_pedido)

class PedidoProductos(models.Model):
    id_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='productos')
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    class Meta:
        unique_together = (('id_pedido', 'id_producto'),)

    def __str__(self):
        return f"Pedido {self.id_pedido} - Producto {self.id_producto}"

class Venta(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE,null=True, blank=True)
    cantidad_vendida = models.PositiveIntegerField(default=0)
    fecha_venta = models.DateField(default=timezone.now)
    def __str__(self):
        return f"Venta de {self.producto.descripcion_producto}"

