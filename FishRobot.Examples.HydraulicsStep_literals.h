#ifdef __cplusplus
extern "C" {
#endif

#define _OMC_LIT0_data ","
static const MMC_DEFSTRINGLIT(_OMC_LIT_STRUCT0,1,_OMC_LIT0_data);
#define _OMC_LIT0 MMC_REFSTRINGLIT(_OMC_LIT_STRUCT0)
#define _OMC_LIT1_data "NoName"
static const MMC_DEFSTRINGLIT(_OMC_LIT_STRUCT1,6,_OMC_LIT1_data);
#define _OMC_LIT1 MMC_REFSTRINGLIT(_OMC_LIT_STRUCT1)
static _index_t _OMC_LIT2_dims[1] = {1};
static const modelica_integer _OMC_LIT2_data[] = {2};
#if (defined(__clang__)  && __clang_major__ >= 17) || (defined(__GNUC__) && __GNUC__ >= 8)
static integer_array const _OMC_LIT2 = {
  1, _OMC_LIT2_dims, (void*) _OMC_LIT2_data, (modelica_boolean) 0
};
#else
/* handle joke compilers */
#define _OMC_LIT2 (base_array_t){1, _OMC_LIT2_dims, (void*) _OMC_LIT2_data, (modelica_boolean) 0}
#endif

#ifdef __cplusplus
}
#endif
