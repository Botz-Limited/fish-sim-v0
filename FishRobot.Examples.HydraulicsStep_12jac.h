/* Jacobians */
static _index_t one_dim[1] = { 1 };
static modelica_real nominal_data[1] = { 1.0 };
static modelica_real start_data[1]   = { 0.0 };
static modelica_real min_data[1]   = { -DBL_MAX };
static modelica_real max_data[1]   = { DBL_MAX };
static const REAL_ATTRIBUTE dummyREAL_ATTRIBUTE = {
  .unit = NULL,
  .displayUnit = NULL,
  .min = {
    .ndims     = 1,
    .dim_size  = one_dim,
    .data      = (void*) min_data,
    .flexible  = FALSE
  },
  .max = {
    .ndims     = 1,
    .dim_size  = one_dim,
    .data      = (void*) max_data,
    .flexible  = FALSE
  },
  .fixed = FALSE,
  .useNominal = FALSE,
  .nominal = {
    .ndims     = 1,
    .dim_size  = one_dim,
    .data      = (void*) nominal_data,
    .flexible  = FALSE
  },
  .start = {
    .ndims     = 1,
    .dim_size  = one_dim,
    .data      = (void*) start_data,
    .flexible  = FALSE
  }
};

#if defined(__cplusplus)
extern "C" {
#endif

/* Jacobian Variables */
#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_NLSJac0 0
int FishRobot_Examples_HydraulicsStep_functionJacNLSJac0_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianNLSJac0(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacNLSJac0_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_NLSJac1 1
int FishRobot_Examples_HydraulicsStep_functionJacNLSJac1_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianNLSJac1(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacNLSJac1_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_ADJ 2
int FishRobot_Examples_HydraulicsStep_functionJacADJ_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianADJ(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacADJ_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_H 3
int FishRobot_Examples_HydraulicsStep_functionJacH_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianH(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacH_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_F 4
int FishRobot_Examples_HydraulicsStep_functionJacF_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianF(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacF_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_D 5
int FishRobot_Examples_HydraulicsStep_functionJacD_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianD(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacD_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_C 6
int FishRobot_Examples_HydraulicsStep_functionJacC_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianC(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacC_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_B 7
int FishRobot_Examples_HydraulicsStep_functionJacB_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianB(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacB_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);


#define FishRobot_Examples_HydraulicsStep_INDEX_JAC_A 8
int FishRobot_Examples_HydraulicsStep_functionJacA_column(DATA* data, threadData_t *threadData, JACOBIAN *thisJacobian, JACOBIAN *parentJacobian);
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianA(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);
void FishRobot_Examples_HydraulicsStep_JacA_DAG(DATA* data, threadData_t *threadData, JACOBIAN *jacobian);

#if defined(__cplusplus)
}
#endif
