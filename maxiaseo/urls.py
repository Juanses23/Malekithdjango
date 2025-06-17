from django.urls import path
from . import views

urlpatterns = [
    path('',views.inicio,name='inicio'),
    path('nuestra_empresa/',views.nuestra_empresa,name='nuestra_empresa'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('olvido/', views.olvido_contrasena_view, name='olvido_contrasena'),
    path('verificar-codigo/', views.verificar_codigo_recuperacion_view, name='verificar_codigo_recuperacion'),
    path('restablecer/', views.restablecer_contrasena_view, name='restablecer_contrasena'),
    path('registro/',views.registro_view,name='registro'),
    path('pedidos/',views.pedidos,name='pedidos'),
    path('perfil/',views.perfil,name='perfil'),
    path('productos/', views.productos_view, name='productos'), # URL para la tienda
    path('carrito/', views.carrito_view, name='carrito_view'),
    path('vaciar_carrito/', views.vaciar_carrito, name='vaciar_carrito'),
    path('eliminar_item_carrito/<str:id_producto>/', views.eliminar_item_carrito, name='eliminar_item_carrito'),
    path('actualizar_cantidad/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('seleccionar-metodo/', views.seleccionar_metodo_pago, name='seleccionar_metodo_pago'),
    path('realizar-compra/', views.realizar_compra, name='realizar_compra'),

    path('admin/', views.admin_view, name='admin_view'),
    path('admin2/', views.admin_view2, name='admin_view2'),
    path('panel_admin/', views.panel_admin, name='panel_admin'),

    path('admin/usuarios/', views.admin_usuarios_view, name='admin_usuarios'),
    path('admin/productos/', views.admin_productos_view, name='admin_productos'),
    path('admin/categorias/', views.admin_categorias_view, name='admin_categorias'),
    path('admin/pedidos/', views.admin_pedidos_view, name='admin_pedidos'),
    path('admin/proveedores/', views.admin_proveedores_view, name='admin_proveedores'),
    path('admin/entradas/', views.admin_entradas_view, name='admin_entradas'),
    path('admin/ventas/', views.admin_ventas_view, name='admin_ventas'),

    path('admin/usuarios/crear/', views.usuario_create, name='usuario_create'),
    path('admin/usuarios/<int:cedula>/editar/', views.usuario_update, name='usuario_update'),
    path('admin/usuarios/<int:cedula>/eliminar/', views.usuario_delete, name='usuario_delete'),

    path('admin/productos/crear/', views.producto_create, name='producto_create'),
    path('admin/productos/<int:id_producto>/editar/', views.producto_update, name='producto_update'),
    path('admin/productos/<int:id_producto>/eliminar/', views.producto_delete, name='producto_delete'),

    
    path('admin/categorias/crear/', views.categoria_create, name='categoria_create'),
    path('admin/categorias/<int:id_categoria>/editar/', views.categoria_update, name='categoria_update'),
    path('admin/categorias/<int:id_categoria>/eliminar/', views.categoria_delete, name='categoria_delete'),

    path('admin/pedidos/crear/', views.pedido_create, name='pedido_create'),
    path('admin/pedidos/editar/<int:pk>/', views.pedido_update, name='pedido_update'),
    path('admin/pedidos/eliminar/<int:pk>/', views.pedido_delete, name='pedido_delete'),

    path('admin/proveedores/crear/', views.proveedor_create, name='proveedor_create'),
    path('admin/proveedores/editar/<int:pk>/', views.proveedor_update, name='proveedor_update'),
    path('admin/proveedores/eliminar/<int:pk>/', views.proveedor_delete, name='proveedor_delete'),

    path('admin/entrada/crear/', views.entrada_create, name='entrada_create'),
    path('admin/entrada/editar/<int:pk>/', views.entrada_update, name='entrada_update'),
    path('admin/entrada/eliminar/<int:pk>/', views.entrada_delete, name='entrada_delete'),
    path('calcular_costo_entrada/', views.calcular_costo_entrada_ajax, name='calcular_costo_entrada_ajax'), # Nueva URL AJAX
    
    path('admin/envio-masivo/', views.admin_envio_masivo, name='admin_envio_masivo'),
]

