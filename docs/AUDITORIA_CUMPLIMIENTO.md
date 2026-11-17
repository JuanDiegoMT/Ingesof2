# Auditoría de cumplimiento · AgroDecide · Prototipo 1

Se releyeron las cuatro páginas de la guía académica y se contrastaron con [la entrega consolidada](ENTREGA_PROTOTIPO_1.md), el código y los archivos de evidencia. La revisión independiente de requisitos, UX y diseño se encomendó al agente de UX. El agente de datos revisó las condiciones de repositorio, sustentación y rúbrica. Otro pase independiente cotejó las operaciones de API con OpenAPI y repitió la suite WSGI. La consolidación contrastó la sección de API con código y salidas de pruebas. «Cubierto» indica que la respuesta es defendible en el alcance indicado, que puede ser de diseño. «Parcial» identifica evidencia o ejecución pendiente.

| Numeral | Resultado de la revisión independiente | Evidencia y acción correctiva |
| --- | --- | --- |
| 1(a) | Cubierto. Un párrafo identifica el problema colombiano, agricultores y administradores, la contextualización de humedad y precios y el valor de la procedencia. | Sección 1(a). Se puede defender como visión del producto. |
| 1(b) | Cubierto. Dos roles, registro público controlado, matriz y distinción entre identidad y permiso. El acceso a sensores y mediciones por ambos roles coincide con el controlador. | 1(b), `agrodecide/http.py` y `agrodecide/aplicacion.py`. Los pronósticos, EVA y el asistente son parte del diseño. |
| 1(c) | Cubierto con 11 historias propias de AgroDecide y revisión INVEST. Las historias de CRUD agrupan operaciones que se pueden desarrollar y probar por separado. | 1(c). La aceptación funcional de las historias futuras requiere sus incrementos respectivos. |
| 1(d) | Cubierto como especificación. Las 11 historias tienen al menos dos criterios Dado–Cuando–Entonces y uno de error, permisos o ausencia de datos. | 1(d). La evidencia de ejecución de los criterios HTTP se registra en 4(g). La API admite el filtro por sensor. El intervalo y el estado vacío se especifican para el cliente. |
| 1(e) | Cubierto. Las actividades y tareas quedan ordenadas en dos incrementos y se marca el MVP del semestre. | 1(e). La disponibilidad del pronóstico depende de datos y evaluación suficientes. |
| 1(f) | Parcial. Las 11 historias tienen estimación Fibonacci, prioridad, versión y estado. La estimación es preliminar y no acredita votación del equipo. | 1(f). Realizar Planning Poker con el equipo y publicar las historias y estimaciones en el tablero real. |
| 2(a) | Parcial. Hay 15 pantallas o estados propios del flujo agrícola y administrativo, cada uno con dos variantes. Se verificaron los 15 destinos del índice y 30 variantes mediante parseo HTML. | 2(a) y `docs/wireframes.html`. Publicar y verificar el enlace de solo lectura con los permisos acordados. |
| 2(b) | Cubierto como diseño. Desde inicio de sesión y registro, el recorrido de agricultor llega al historial y a la predicción, y el de administrador a ambos recursos. Incluye validaciones, faltantes, 401 y 403. | 2(b), diagrama y wireframes. El cliente diseñará la selección de sensor e intervalo y consumirá el filtro por sensor de la API. |
| 2(c) | Cubierto. Se decide una web adaptable para móviles con acceso al servidor local. Se justifica por despliegue, mantenimiento y capacidad requerida al dispositivo. | 2(c). Hay base para defender el coste de las alternativas y cuándo se necesitaría modo sin conexión. |
| 3(a) | Cubierto. El diagrama muestra navegadores web y móvil, cliente adaptable, API, SQLite, ML y Ollama. Se distinguen integración propuesta y API existente. | 3(a), `agrodecide/http.py`, `agrodecide/aplicacion.py` y `agrodecide/repositorio.py`. Los adaptadores de ingestión y RAG siguen proyectados. |
| 3(b) | Cubierto. Trece términos, context map y agregado con raíz Sensor, Medición como entidad y objetos de valor propuestos. | 3(b); el código respalda las restricciones persistidas, no la implementación completa del agregado. Revisar el invariante propuesto de profundidad antes de usar lecturas de un sensor trasladado para inferencia. |
| 3(c) | Cubierto como diseño. Los dos diagramas muestran dominio y aplicación y los principios SOLID se vinculan a problemas concretos. | 3(c). Se ajustó el diagrama de aplicación a las clases existentes. Los objetos de valor y contratos explícitos se documentan como diseño. |
| 3(d) | Cubierto como diseño. Strategy permite comparar algoritmos bajo la misma evaluación y Adapter delimita formatos y unidades de las fuentes. Ambos incluyen participantes y propósito. | 3(d). Mantener carácter de diseño hasta verificar equivalencias con clases reales. |
| 3(e) | Cubierto como diseño. Tres escenarios de seis elementos, con seguridad, rendimiento y disponibilidad, cada uno con táctica y medida. | 3(e). La prueba de autorización verificó que la escritura rechazada conserva el listado. Ejecutar las mediciones de latencia y contingencia en el equipo de sustentación. |
| 4(a) | Verificado para 13 operaciones de negocio del Prototipo 1. Contrato OpenAPI con bearerAuth, errores y ejemplos cotejados. Swagger Editor activo reportó cero diagnósticos y detectó el error en el control. | §4(a), `openapi.yaml` y captura. Incorporar operaciones de EVA, pronósticos y asistente cuando estén en el backend. |
| 4(b) | Cubierto para la API local. Los dos CRUD usan controlador, casos de uso, validación de dominio y persistencia. | §4(b), código y comprobaciones de §4(g). |
| 4(c) | Cubierto para el backend local. Registro, login, emisión y expiración JWT y hash Argon2id. | §4(c), código de seguridad y evidencia de integración. |
| 4(d) | Cubierto para la API local. Perfil exclusivo agrícola y escrituras exclusivas administrativas. | §4(d,g). La matriz, el controlador y la respuesta observada respaldan la distinción 401/403. |
| 4(e) | Cubierto para configuración local. Entrada validada, errores uniformes, origen explícito y clave por entorno. | §4(e). Validar permisos de despliegue, límites de login y rotación de claves antes de producción. |
| 4(f) | Cubierto por la alternativa descrita en la guía para entornos sin despliegue. | §4(f). Configurar proxy y certificado final antes de exponer el backend. |
| 4(g) | Verificado mediante Newman. Colección exportada y ejecutada por HTTP. Se registraron 22 solicitudes y 40 aserciones sin fallos. | §4(g). Registrar la ejecución gráfica si el profesor la exige para la sustentación. |
| 4(h) | Opcional pendiente. La descarga SIPSA es evidencia de datos, y el adaptador externo se propone. | §4(h), anexo A. Implementar conexión solo si se decide optar por la bonificación. |
| 5(a) | URL del repositorio de destino verificada. GitHub lo identifica como público. | §5(a), [repositorio](https://github.com/JuanDiegoMT/Ingesof2). |
| 5(b) | Parcial. Arranque y publicación del contrato reproducidos según README. Faltan participantes y enlaces remotos. | §5(b), README. Completar datos oficiales y probar desde otra instalación. |
| 5(c) | No verificable. La estrategia de ramas es una propuesta de proceso. | §5(c). Obtener historial, contribuciones y evidencia de pull requests revisadas. |
| 5(d) | Parcial. Exclusiones locales documentadas, historial ausente. | §5(d) y `.gitignore`. Revisar commits y referencias en el repositorio académico. |
| 6(a) | Cubierto como estructura. Secciones en orden y corte de anexos explícito. | §6(a). Exportación de prueba del cuerpo en A4 de 14 páginas, incluida la portada. Mantener el corte de anexos al preparar la versión formal. |
| 6(b) | Cubierto como plan de sustentación. Incluye las tres franjas de cinco minutos, participación y preguntas. | §6(b). Ensayar con todos los integrantes en el equipo que servirá para la demostración. |
| Rúbrica | Cubierta. Los pesos 20, 10, 25, 30, 5 y 10 suman 100 %. | §7. Estados descriptivos sin nota atribuida. |
| Lista de verificación | Cubierta como lista. Diez elementos cotejados con la página 4 y vinculados a una evidencia o acción. | §8. Los estados pendientes figuran en las filas correspondientes. |

## Contraste de afirmaciones y evidencias

- **Historias y alcance.** Las operaciones de identidad y monitoreo corresponden al primer incremento. Las vistas son wireframes. Las historias de mercado, EVA, predicción y asistencia quedan como diseño de producto con evaluación de datos por fuera del backend.
- **Dominio y diseño.** El agregado Serie de humedad, los objetos de valor y los patrones GoF se declaran diseño. Las restricciones concretas de persistencia se explican con el código.
- **Predicciones.** El anexo A registra el piloto con boletines SIPSA y el ensayo de humedad sobre la tabla original publicada. La sensibilidad sin registros COMP no produjo ventanas elegibles, por lo que falta evidencia de procedencia para validar el resultado como desempeño de campo. El horizonte de 24 h se mide desde el corte y la ventana solo usa el pasado. La serie mayorista usa una variedad, un mercado y frecuencia semanal.
- **Fuentes y asistente.** EVA se usa como agregado municipal, CROPWAT como herramienta y los datasets IoT como telemetría candidata. Ollama y RAG se documentan como propuesta, con lectura acotada y trazabilidad.
- **Git y proceso.** Las afirmaciones sobre contribuciones, accesos y enlaces académicos quedan pendientes de la evidencia del repositorio real.

## Correcciones prioritarias

1. Preparar la ejecución de demostración en Postman con una base descartable y conservar la especificación validada.
2. Incorporar los datos del equipo, publicar los wireframes con permisos de lectura y enlazar el tablero real. Inspeccionar historial y revisiones.
3. Aclarar el origen de la marca COMP con los autores de la fuente y repetir la evaluación con registros de campo cuya procedencia se confirme. Ampliar el piloto SIPSA antes de seleccionar un modelo operativo.
4. Construir el incremento de cliente e inferencia local. Medir los escenarios de calidad y ensayar el guion de sustentación.
