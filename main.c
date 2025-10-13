#include <stddef.h> // para size_t
#include <stdio.h>  // para los ficheros
#include <string.h> // para strtok
#include <ctype.h>  // para isdigit
#include <stdlib.h> // para malloc
#include <time.h>   // para fechas
#include "funciones.h" // para calculos estadisticos
#include <math.h> // para sqrt


int main(void) {
    FILE *f = fopen("C:/Users/manu3/python/salida.txt", "r");
    if (!f) {
        perror("No se pudo abrir");
        return 1;
    }
    //cuento la cantidad de lineas con datos para luego hacer los malloc:
    char linea[256];
    unsigned int contador = 0;

    // descartar cabecera
    fgets(linea, sizeof linea, f);

    while (fgets(linea, sizeof linea, f)) // no se cumple si no hay linea disponible
    {
        // si empieza con dígito -> es una línea de datos
        if (isdigit((unsigned char)*linea))
        {
            contador++;
        }
    }
    //reservo memoria
    double *tiempo = malloc(contador*sizeof(double));
    double *temp = malloc(contador*sizeof(double));


    //reservo memoria para las fechas
    char **fecha;

    //guardo memoria para el vector de fechas (el cual consistira de cadenas de 19 caracteres)
    fecha = malloc(contador * sizeof(char *));

    for (int i = 0; i < contador; i++)
    {
        fecha[i] = malloc(19 * sizeof(char)); // hasta 9 caracteres + '\0' por cada parte
    }

    //ahora procedo a guardar los datos en los vectores fecha, tiempo y temp
    //reinicio el cursor y el contador para hace un while similar
    rewind(f);
    // descartar cabecera
    fgets(linea, sizeof linea, f);
    //reinicio contador
    contador = 0;
    while (fgets(linea, sizeof linea, f)) // no se cumple si no hay linea disponible
    {

        if (isdigit((unsigned char)*linea)) // si empieza con dígito -> es una línea de datos
        {
            char *token_fecha = strtok(linea,",");
            char *token_tiempo = strtok(NULL,",");
            char *token_temp = strtok(NULL,",");

            strcpy(fecha[contador],token_fecha);
            tiempo[contador] = atof(token_tiempo);
            temp[contador] = atof(token_temp);

            printf("Fecha y hora: %s ",fecha[contador]);
            printf("| Tiempo: %10.2lf ",tiempo[contador]);
            printf("| Temperatura: %lf\n",temp[contador]);

            contador++;
        }
    }
    printf("\nLa cantidad de lecturas realizadas por la estacion es: %d\n",contador);
    //calculos estadisticos:

    size_t *indices = DevolverMaxMin(temp,contador);
    //printf("el indice donde se detecto el max es %llu y el indice donde se detecto el min es %llu (contando desde cero)\n",indices[0],indices[1]);

    printf("la temperatura maxima fue de %lf y se detecto en la fecha y hora %s\n",temp[indices[0]],fecha[indices[0]]);

    printf("la temperatura minima fue de %lf y se detecto en la fecha y hora %s\n",temp[indices[1]],fecha[indices[1]]);

    double media = DevolverMedia(temp,contador);
    printf("la temperatura media fue de %lf\n",media);
    printf("la temperatura moda fue de %lf\n",DevolverModa(temp,contador));
    printf("el desvio tipico alrededor de la media fue de %lf\n",sqrt(Varianza(temp,contador,media)));

    OrdenarVector(temp,contador);

    if (contador % 2 != 0) printf("la temperatura Mediana fue de %lf\n",temp[contador/2]);
    else printf("la temperatura Mediana fue de %lf\n",(temp[contador/2-1]+temp[contador/2])/2);

    printf("El vector de temperaturas ordenado de menor a mayor es: \n");
    for (int i=0; i<contador;i++)
    {
        printf("%lf\n",temp[i]);
    }


    fclose(f);
    for (int i = 0; i < contador; i++)
    {
        free(fecha[i]);
    }
    free(fecha);
    free(tiempo);
    free(temp);
    return 0;
}
