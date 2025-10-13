#include <stdio.h>

/******************************************************************
Devuelve un array con los indices corresp. a temp. maxima y mínima
******************************************************************/
size_t *DevolverMaxMin(double *vec, unsigned int n) //n es la longitud del vector
{


    size_t *a;
    a = (size_t *)malloc(sizeof(size_t)*2);
    if (vec == NULL || n == 0) {
        return 0;
    }
    size_t j= 0;
    size_t k= 0;
    double max = vec[0];
    double min = vec[0];

    for (int i = 1; i < n; i++) {
        if (vec[i] > max) {
            max = vec[i];
            j=i;
        }
        if (vec[i] < min) {
            min = vec[i];
            k=i;
        }
    }
    a[0] = j;
    a[1] = k;
    return a;
}



/******************************************************************
          Devuelve la media de un array de doubles
******************************************************************/
double DevolverMedia(double *v, unsigned int n)//n es la longitud del vector
{
    double media = 0;
    for (int i=0; i<n;i++)
    {
        media +=v[i];
    }
    media /= n;
    return media;
}



/******************************************************************
         Devuelve la moda de un array de doubles
******************************************************************/
double DevolverModa(double *v, int n)//n es la longitud del vector
{
    int maxCount = 0; // inicio la puja del elemento con mas apariciones
    double moda = v[0];  // declaro la moda como el elemento inicial

    for (int i = 0; i < n; i++) // bucle para el elemento i
    {
        int count = 0; //inicio el contador de apariciones del elemento i
        for (int j = 0; j < n; j++)
        {
            if (v[i] == v[j]) count++; //cuento
        }
        if (count > maxCount) // aumento la puja si es preciso
        {
            maxCount = count;
            moda = v[i];
        }
    }
    return moda;
}


/******************************************************************
         Ordena un vector de doubles de manera creciente
******************************************************************/
void OrdenarVector(double *v, int n)//n es la longitud del vector
{
    for (int i=0; i<n;i++)
    {
        for (int j=i; j>0; j--)
        {
            if (v[j-1]>v[j]) IntercambiarElementos(v,n,j-1,j);
        }
    }
}


/******************************************************************
    Devuelve un array de doubles con dos elementos intercambiados
******************************************************************/
int IntercambiarElementos(double *v, int n, int i, int j)//n es la longitud del vector
{
    double temporal = v[i]; //variable temporal
    v[i] = v[j];
    v[j] = temporal;
}


/******************************************************************
         Devuelve la varianza de un array de doubles
******************************************************************/
double Varianza(double *v, int n, double media) //n es la longitud del vector
{
    double varianza = 0;
    for (int i=0; i<n; i++)
    {
        varianza+=(v[i]-media)*(v[i]-media);
    }
    return varianza/n;
}


