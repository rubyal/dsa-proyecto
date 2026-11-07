Definición de solicitudes no urgentes y variable objetivo
El sistema NYC 311 está destinado a la recepción y gestión de solicitudes de servicios no urgentes. Por esta razón, las solicitudes registradas en este sistema se consideran no urgentes por definición, sin necesidad de establecer una clasificación adicional de urgencia para seleccionar los registros. En consecuencia, el proyecto se concentra en anticipar el comportamiento de la demanda de estas solicitudes, sin incluir emergencias que deben atenderse mediante otros canales.
La variable objetivo del proyecto se denomina nivel_demanda y corresponde a una clasificación de la demanda semanal de solicitudes NYC 311 en tres categorías: Baja, Media y Alta.
La clasificación se realiza para cada uno de los cinco boroughs de Nueva York, debido a las diferencias existentes en los volúmenes habituales de solicitudes. Para ello, se utiliza como referencia el promedio de solicitudes de las 52 semanas anteriores de cada distrito.
La demanda relativa se calcula mediante la siguiente expresión:
Demanda relativa = Solicitudes de la semana / Promedio de solicitudes de las 52 semanas anteriores
De esta manera, un valor superior a 1 indica que el volumen de solicitudes de la semana está por encima de su promedio histórico, mientras que un valor inferior a 1 representa una demanda por debajo de ese promedio.
Para construir la variable objetivo, se utilizaron los registros correspondientes a 2022–2025. Las primeras 52 semanas de cada borough se reservaron como historial para calcular los promedios móviles, dejando 780 observaciones semanales disponibles para la clasificación durante 2023–2025.
Los umbrales de clasificación se definieron mediante los percentiles 33 y 67 de la demanda relativa de cada borough, calculados únicamente con información de 2023–2024. Estos límites se mantuvieron constantes al clasificar las observaciones de 2025, evitando utilizar información futura en su definición.
La asignación de las categorías se realiza de la siguiente manera:
•	Demanda Baja: demanda relativa inferior al percentil 33 del borough.
•	Demanda Media: demanda relativa entre los percentiles 33 y 67.
•	Demanda Alta: demanda relativa superior al percentil 67.
Esta metodología permite establecer los niveles de demanda en función del comportamiento histórico de cada distrito, sin imponer umbrales absolutos iguales para toda la ciudad.
La variable nivel_demanda constituye la etiqueta del modelo de clasificación supervisada. El objetivo es anticipar el nivel de demanda de la semana siguiente utilizando exclusivamente información disponible hasta la semana anterior.

