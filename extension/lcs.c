#include <Python.h>
#include <math.h>

wchar_t *lcommon(const wchar_t *string1, const wchar_t *string2) {
	int strlen1 = wcslen(string1);
	int strlen2 = wcslen(string2);
	int i, j, end=0;
	int longest = 0;
	int **ptr = (int **)malloc((strlen1 + 1) * sizeof(int *));
    wchar_t *res;

	for (i = 0; i < strlen1 + 1; i++)
		ptr[i] = (int *)calloc((strlen2 + 1), sizeof(int));

	for (i = 1; i < strlen1 + 1; i++) {
		for (j = 1; j < strlen2 + 1; j++) {
			if (string1[i-1] == string2[j-1]) {
				ptr[i][j] = ptr[i-1][j-1] + 1;
                if (ptr[i][j] > longest) {
                    longest = ptr[i][j];
                    end = i;
                }
            }
            else {
				ptr[i][j] = 0;
			}
		}
	}
	for (i = 0; i < strlen1 + 1; i++)
		free(ptr[i]);
	free(ptr);
    
    res = (wchar_t *)calloc((longest + 1), sizeof(wchar_t));
    
	wcsncpy(res, &(string1[end-longest]), longest);
    //printf("substring from %d, length is %d\n", end-longest, longest);
	return res;
}

static PyObject * lcs_function(PyObject *self, PyObject *args) {
    const wchar_t *_a, *_b;
    wchar_t *res = NULL;
    PyObject *ret = NULL;
    int strlen, i;
    if (!PyArg_ParseTuple(args, "uu", &_a, &_b))
        return NULL;

    //printf("input string1 is %ls\n", _a);
    //printf("input string2 is %ls\n", _b);
    res = lcommon(_a, _b);
    ret = Py_BuildValue("u", res);
    free(res);
    return ret; 
}


static PyObject * cosine_function(PyObject *self, PyObject *args) {
    PyObject * listObj1; /* the list as vector1 */
    PyObject * listObj2; /* the list as vector2 */
    PyObject * doubleObj;  /* one double float in the list */
    int vectorSize1 = 0;
    int vectorSize2 = 0;
    int i;
    double *vector1 = NULL;
    double *vector2 = NULL;
    double dot = 0, norm1 = 0, norm2 = 0, cosineDistance=0;
    
    PyObject *ret = NULL;
    /* the O! parses for a Python object (listObj) checked
        to be of type PyList_Type */
    if (! PyArg_ParseTuple( args, "O!O!", &PyList_Type, &listObj1, &PyList_Type, &listObj2)) 
        return NULL;
    
    vectorSize1 = PyList_Size(listObj1);
    vectorSize2 = PyList_Size(listObj2);
    if (vectorSize1 <= 0 || vectorSize2 <= 0){
        printf("The size of the two vectors must not be 0!");
        return 0;
    }
    
    if (vectorSize1 != vectorSize2){
        printf("The size of the two vectors must be same!");
        return 0;
    }
       
    //printf("input size1 is %d\n", vectorSize1);
    //printf("input size2 is %d\n", vectorSize2);
    
    vector1 = (double *)calloc(vectorSize1, sizeof(double));
    vector2 = (double *)calloc(vectorSize2, sizeof(double));
    
    for (i = 0; i < vectorSize1; i++){
        doubleObj = PyList_GetItem(listObj1, i); 
        vector1[i] = PyFloat_AsDouble(doubleObj); 
        doubleObj = PyList_GetItem(listObj2, i);         
        vector2[i] = PyFloat_AsDouble(doubleObj);
    }
    
    for (i = 0; i < vectorSize1; i++){
        dot += vector1[i] * vector2[i];
        norm1 += vector1[i] * vector1[i];
        norm2 += vector2[i] * vector2[i];   
    }
    
    cosineDistance = dot / (sqrt(norm1) * sqrt(norm2));
    
    
    free(vector1);
    free(vector2);
    
    
    ret = Py_BuildValue("d", cosineDistance);

    return ret; 
}

static PyMethodDef lcsMethods[] = {
    {
         "lcs",
         lcs_function,
         METH_VARARGS,
         ""
    },
    {
         "cosine",
         cosine_function,
         METH_VARARGS,
         ""
    },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef lcs = {
    PyModuleDef_HEAD_INIT,
    "lcs",
    NULL,
    -1,
    lcsMethods
};

PyMODINIT_FUNC PyInit_lcs(void)
{
    PyObject *m;
    m = PyModule_Create(&lcs);
    if (m == NULL)
        return NULL;
    printf("init lcs module\n");
    return m;
}