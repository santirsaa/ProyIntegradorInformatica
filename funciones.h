#ifndef FUNCIONES_H_INCLUDED
#define FUNCIONES_H_INCLUDED

size_t *DevolverMaxMin(double *vec, unsigned int n);
double DevolverMedia(double *vec, unsigned int n);
double DevolverModa(const double *v, int n);
void OrdenarVector(double *v, int n);
int IntercambiarElementos(double *v, int n, int i, int j);
double Varianza(double *v, int n, double media);


#endif // FUNCIONES_H_INCLUDED
