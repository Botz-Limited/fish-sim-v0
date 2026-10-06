/* Non Linear Systems */
#include "FishRobot.Examples.HydraulicsStep_model.h"
#include "FishRobot.Examples.HydraulicsStep_12jac.h"
#include "simulation/jacobian_util.h"
#include "simulation/arrayIndex.h"

#if defined(__cplusplus)
extern "C" {
#endif

/* inner equations */

/*
equation index: 40
type: SIMPLE_ASSIGN
reliefLR.dp_over = 0.5 * (reliefLR.dp + sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0) - reliefLR.p_set)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_40(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,40};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[174]] /* reliefLR.p_set PARAM */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[173]] /* reliefLR.dp_smooth PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0) was %g should be >= 0", tmp2);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[77]] /* reliefLR.dp_over variable */) = (0.5) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) + sqrt(tmp2) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[174]] /* reliefLR.p_set PARAM */));
  threadData->lastEquationSolved = 40;
}
/*
equation index: 41
type: SIMPLE_ASSIGN
reliefLR.V_flow = reliefLR.G_leak * reliefLR.dp + reliefLR.G_open * reliefLR.dp_over
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_41(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,41};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[75]] /* reliefLR.V_flow variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[169]] /* reliefLR.G_leak PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */)) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[170]] /* reliefLR.G_open PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[77]] /* reliefLR.dp_over variable */));
  threadData->lastEquationSolved = 41;
}
/*
equation index: 42
type: SIMPLE_ASSIGN
reliefRL.dp_over = 0.5 * (reliefRL.dp + sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0) - reliefRL.p_set)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_42(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,42};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[180]] /* reliefRL.p_set PARAM */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[179]] /* reliefRL.dp_smooth PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0) was %g should be >= 0", tmp2);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[81]] /* reliefRL.dp_over variable */) = (0.5) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) + sqrt(tmp2) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[180]] /* reliefRL.p_set PARAM */));
  threadData->lastEquationSolved = 42;
}
/*
equation index: 43
type: SIMPLE_ASSIGN
reliefRL.V_flow = reliefRL.G_leak * reliefRL.dp + reliefRL.G_open * reliefRL.dp_over
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_43(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,43};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[79]] /* reliefRL.V_flow variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[175]] /* reliefRL.G_leak PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */)) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[176]] /* reliefRL.G_open PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[81]] /* reliefRL.dp_over variable */));
  threadData->lastEquationSolved = 43;
}
/*
equation index: 44
type: SIMPLE_ASSIGN
pipeR.dp = (pipeR.R_lam + pipeR.R_turb * sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0)) * pipeR.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_44(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,44};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[157]] /* pipeR.V_flow_small PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0) was %g should be >= 0", tmp2);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[64]] /* pipeR.dp variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[155]] /* pipeR.R_lam PARAM */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[156]] /* pipeR.R_turb PARAM */)) * (sqrt(tmp2))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */));
  threadData->lastEquationSolved = 44;
}
/*
equation index: 45
type: SIMPLE_ASSIGN
Q_pump = reliefLR.V_flow - (reliefRL.V_flow + pipeR.V_flow)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_45(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,45};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[21]] /* Q_pump variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[75]] /* reliefLR.V_flow variable */) - ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[79]] /* reliefRL.V_flow variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */));
  threadData->lastEquationSolved = 45;
}
/*
equation index: 46
type: SIMPLE_ASSIGN
pipeL.V_flow = reliefRL.V_flow - (reliefLR.V_flow - Q_pump)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_46(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,46};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[79]] /* reliefRL.V_flow variable */) - ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[75]] /* reliefLR.V_flow variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[21]] /* Q_pump variable */));
  threadData->lastEquationSolved = 46;
}
/*
equation index: 47
type: SIMPLE_ASSIGN
pipeL.dp = (pipeL.R_lam + pipeL.R_turb * sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0)) * pipeL.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_47(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,47};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[146]] /* pipeL.V_flow_small PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0) was %g should be >= 0", tmp2);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[58]] /* pipeL.dp variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[144]] /* pipeL.R_lam PARAM */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[145]] /* pipeL.R_turb PARAM */)) * (sqrt(tmp2))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */));
  threadData->lastEquationSolved = 47;
}
/*
equation index: 48
type: SIMPLE_ASSIGN
reliefRL.port_a.p = pipeR.port_b.p + pipeR.dp
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_48(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,48};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[65]] /* pipeR.port_b.p variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[64]] /* pipeR.dp variable */);
  threadData->lastEquationSolved = 48;
}
/*
equation index: 49
type: SIMPLE_ASSIGN
reliefRL.port_b.p = reliefRL.port_a.p + reliefLR.dp
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_49(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,49};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */);
  threadData->lastEquationSolved = 49;
}
/*
equation index: 50
type: SIMPLE_ASSIGN
pump.dp_pump = reliefRL.port_a.p + reliefLR.dp - reliefRL.port_b.p - reliefRL.dp
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_50(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,50};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */);
  threadData->lastEquationSolved = 50;
}

void residualFunc67(RESIDUAL_USERDATA* userData, const double* xloc, double* res, const int* iflag)
{
  DATA *data = userData->data;
  threadData_t *threadData = userData->threadData;
  const int equationIndexes[2] = {1,67};
  int i,j;
  /* iteration variables */
  for (i=0; i<3; i++) {
    if (isinf(xloc[i]) || isnan(xloc[i])) {
      errorStreamPrint(OMC_LOG_NLS, 0, "residualFunc67: Iteration variable `%s` is inf or nan.",
        modelInfoGetEquation(&data->modelData->modelDataXml, 67).vars[i]);
      for (j=0; j<3; j++) {
        res[j] = NAN;
      }
      throwStreamPrintWithEquationIndexes(threadData, omc_dummyFileInfo, equationIndexes, "residualFunc67 failed at time=%.15g.\nFor more information please use -lv LOG_NLS.", data->localData[0]->timeValue);
      return;
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */) = xloc[0];
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) = xloc[1];
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) = xloc[2];
  /* backup outputs */
  /* pre body */
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_40(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_41(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_42(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_43(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_44(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_45(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_46(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_47(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_48(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_49(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_50(data, threadData);
  /* body */
  res[0] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */) + (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[59]] /* pipeL.port_b.p variable */)) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[58]] /* pipeL.dp variable */);
  threadData->lastEquationSolved = 53;
  res[1] = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[164]] /* pump.D PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */)) + ((-(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[167]] /* pump.k_leak PARAM */))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */)) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[21]] /* Q_pump variable */);
  threadData->lastEquationSolved = 52;
  res[2] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */);
  threadData->lastEquationSolved = 51;
  /* restore known outputs */
  threadData->lastEquationSolved = 67;
}

OMC_DISABLE_OPT
void initializeSparsePatternNLS67(NONLINEAR_SYSTEM_DATA* inSysData)
{
  int i=0;
  const int colPtrIndex[1+3] = {0,3,3,3};
  const int rowIndex[9] = {0,1,2,0,1,2,0,1,2};
  /* sparsity pattern available */
  inSysData->isPatternAvailable = TRUE;
  inSysData->sparsePattern = allocSparsePattern(3, 9, 3);
  
  /* write lead index of compressed sparse column */
  memcpy(inSysData->sparsePattern->leadindex, colPtrIndex, (3+1)*sizeof(unsigned int));
  
  for(i=2;i<3+1;++i)
    inSysData->sparsePattern->leadindex[i] += inSysData->sparsePattern->leadindex[i-1];
  
  /* call sparse index */
  memcpy(inSysData->sparsePattern->index, rowIndex, 9*sizeof(unsigned int));
  
  /* write color array */
  /* color 1 with 1 columns */
  const int indices_1[1] = {2};
  for(i=0; i<1; i++)
    inSysData->sparsePattern->colorCols[indices_1[i]] = 1;
  
  /* color 2 with 1 columns */
  const int indices_2[1] = {1};
  for(i=0; i<1; i++)
    inSysData->sparsePattern->colorCols[indices_2[i]] = 2;
  
  /* color 3 with 1 columns */
  const int indices_3[1] = {0};
  for(i=0; i<1; i++)
    inSysData->sparsePattern->colorCols[indices_3[i]] = 3;
}

void freeSparsePatternNLS67(NONLINEAR_SYSTEM_DATA* inSysData)
{
  if (inSysData->isPatternAvailable) {
    freeSparsePattern(inSysData->sparsePattern);
    free(inSysData->sparsePattern);
    inSysData->sparsePattern = NULL;
    inSysData->isPatternAvailable = FALSE;
  }
}
OMC_DISABLE_OPT
void initializeNonlinearPatternNLS67(NONLINEAR_SYSTEM_DATA* inSysData)
{
  int i=0;
  inSysData->nonlinearPattern = (NONLINEAR_PATTERN*) malloc(sizeof(NONLINEAR_PATTERN));
  inSysData->nonlinearPattern->numberOfVars = 3;
  inSysData->nonlinearPattern->numberOfEqns = 3;
  inSysData->nonlinearPattern->numberOfNonlinear = 7;
  inSysData->nonlinearPattern->indexVar = (unsigned int*) malloc((3+1)*sizeof(unsigned int));
  inSysData->nonlinearPattern->indexEqn = (unsigned int*) malloc((3+1)*sizeof(unsigned int));
  inSysData->nonlinearPattern->columns = (unsigned int*) malloc(7*sizeof(unsigned int));
  inSysData->nonlinearPattern->rows = (unsigned int*) malloc(7*sizeof(unsigned int));
  /* initialize and accumulate index vectors */
  const int index_var[1+3] = {0,3,3,1};
  const int index_eqn[1+3] = {0,3,3,1};
  memcpy(inSysData->nonlinearPattern->indexVar, index_var, (3+1)*sizeof(unsigned int));
  memcpy(inSysData->nonlinearPattern->indexEqn, index_eqn, (3+1)*sizeof(unsigned int));
  for(i=2;i<3+1;++i)
    inSysData->nonlinearPattern->indexVar[i] += inSysData->nonlinearPattern->indexVar[i-1];
  for(i=2;i<3+1;++i)
    inSysData->nonlinearPattern->indexEqn[i] += inSysData->nonlinearPattern->indexEqn[i-1];
  /* initialize columns and rows */
  const int columns[7] = {0,1,2,0,1,2,0};
  const int rows[7] = {0,1,2,0,1,0,1};
  memcpy(inSysData->nonlinearPattern->columns, columns, 7*sizeof(unsigned int));
  memcpy(inSysData->nonlinearPattern->rows, rows, 7*sizeof(unsigned int));
}

OMC_DISABLE_OPT
void initializeStaticDataNLS67(DATA* data, threadData_t *threadData, NONLINEAR_SYSTEM_DATA *sysData, modelica_boolean initSparsePattern, modelica_boolean initNonlinearPattern)
{
  int i=0;
  /* static nls data for pipeR.V_flow */
  sysData->nominal[i] = getNominalFromScalarIdx(data->simulationInfo, data->modelData, VAR_KIND_VARIABLE, 63 /* pipeR.V_flow */);
  sysData->min[i]     = getMinFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 63 /* pipeR.V_flow */);
  sysData->max[i++]   = getMaxFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 63 /* pipeR.V_flow */);
  /* static nls data for reliefRL.dp */
  sysData->nominal[i] = getNominalFromScalarIdx(data->simulationInfo, data->modelData, VAR_KIND_VARIABLE, 80 /* reliefRL.dp */);
  sysData->min[i]     = getMinFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 80 /* reliefRL.dp */);
  sysData->max[i++]   = getMaxFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 80 /* reliefRL.dp */);
  /* static nls data for reliefLR.dp */
  sysData->nominal[i] = getNominalFromScalarIdx(data->simulationInfo, data->modelData, VAR_KIND_VARIABLE, 76 /* reliefLR.dp */);
  sysData->min[i]     = getMinFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 76 /* reliefLR.dp */);
  sysData->max[i++]   = getMaxFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 76 /* reliefLR.dp */);
  /* initial sparse pattern */
  if (initSparsePattern) {
    initializeSparsePatternNLS67(sysData);
  }
  if (initNonlinearPattern) {
    initializeNonlinearPatternNLS67(sysData);
  }
}

OMC_DISABLE_OPT
void freeStaticDataNLS67(DATA* data, threadData_t *threadData, NONLINEAR_SYSTEM_DATA *sysData)
{
  freeSparsePatternNLS67(sysData);
}

OMC_DISABLE_OPT
void getIterationVarsNLS67(DATA* data, double *array)
{
  array[0] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  array[1] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */);
  array[2] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */);
}


/* inner equations */

/*
equation index: 142
type: SIMPLE_ASSIGN
reliefLR.dp_over = 0.5 * (reliefLR.dp + sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0) - reliefLR.p_set)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_142(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,142};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[174]] /* reliefLR.p_set PARAM */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[173]] /* reliefLR.dp_smooth PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0) was %g should be >= 0", tmp2);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[77]] /* reliefLR.dp_over variable */) = (0.5) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) + sqrt(tmp2) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[174]] /* reliefLR.p_set PARAM */));
  threadData->lastEquationSolved = 142;
}
/*
equation index: 143
type: SIMPLE_ASSIGN
reliefLR.V_flow = reliefLR.G_leak * reliefLR.dp + reliefLR.G_open * reliefLR.dp_over
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_143(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,143};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[75]] /* reliefLR.V_flow variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[169]] /* reliefLR.G_leak PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */)) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[170]] /* reliefLR.G_open PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[77]] /* reliefLR.dp_over variable */));
  threadData->lastEquationSolved = 143;
}
/*
equation index: 144
type: SIMPLE_ASSIGN
reliefRL.dp_over = 0.5 * (reliefRL.dp + sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0) - reliefRL.p_set)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_144(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,144};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[180]] /* reliefRL.p_set PARAM */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[179]] /* reliefRL.dp_smooth PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0) was %g should be >= 0", tmp2);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[81]] /* reliefRL.dp_over variable */) = (0.5) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) + sqrt(tmp2) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[180]] /* reliefRL.p_set PARAM */));
  threadData->lastEquationSolved = 144;
}
/*
equation index: 145
type: SIMPLE_ASSIGN
reliefRL.V_flow = reliefRL.G_leak * reliefRL.dp + reliefRL.G_open * reliefRL.dp_over
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_145(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,145};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[79]] /* reliefRL.V_flow variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[175]] /* reliefRL.G_leak PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */)) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[176]] /* reliefRL.G_open PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[81]] /* reliefRL.dp_over variable */));
  threadData->lastEquationSolved = 145;
}
/*
equation index: 146
type: SIMPLE_ASSIGN
pipeL.dp = (pipeL.R_lam + pipeL.R_turb * sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0)) * pipeL.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_146(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,146};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[146]] /* pipeL.V_flow_small PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0) was %g should be >= 0", tmp2);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[58]] /* pipeL.dp variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[144]] /* pipeL.R_lam PARAM */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[145]] /* pipeL.R_turb PARAM */)) * (sqrt(tmp2))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */));
  threadData->lastEquationSolved = 146;
}
/*
equation index: 147
type: SIMPLE_ASSIGN
Q_pump = reliefLR.V_flow + pipeL.V_flow - reliefRL.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_147(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,147};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[21]] /* Q_pump variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[75]] /* reliefLR.V_flow variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[79]] /* reliefRL.V_flow variable */);
  threadData->lastEquationSolved = 147;
}
/*
equation index: 148
type: SIMPLE_ASSIGN
pipeR.V_flow = reliefLR.V_flow - (reliefRL.V_flow + Q_pump)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_148(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,148};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[75]] /* reliefLR.V_flow variable */) - ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[79]] /* reliefRL.V_flow variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[21]] /* Q_pump variable */));
  threadData->lastEquationSolved = 148;
}
/*
equation index: 149
type: SIMPLE_ASSIGN
pipeR.dp = (pipeR.R_lam + pipeR.R_turb * sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0)) * pipeR.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_149(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,149};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[157]] /* pipeR.V_flow_small PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0) was %g should be >= 0", tmp2);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[64]] /* pipeR.dp variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[155]] /* pipeR.R_lam PARAM */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[156]] /* pipeR.R_turb PARAM */)) * (sqrt(tmp2))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */));
  threadData->lastEquationSolved = 149;
}
/*
equation index: 150
type: SIMPLE_ASSIGN
reliefRL.port_b.p = pipeL.port_b.p + pipeL.dp
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_150(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,150};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[59]] /* pipeL.port_b.p variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[58]] /* pipeL.dp variable */);
  threadData->lastEquationSolved = 150;
}
/*
equation index: 151
type: SIMPLE_ASSIGN
reliefRL.port_a.p = reliefRL.port_b.p - reliefLR.dp
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_151(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,151};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */);
  threadData->lastEquationSolved = 151;
}
/*
equation index: 152
type: SIMPLE_ASSIGN
pump.dp_pump = reliefRL.port_a.p + reliefLR.dp - reliefRL.port_b.p - reliefRL.dp
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_152(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,152};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */);
  threadData->lastEquationSolved = 152;
}

void residualFunc169(RESIDUAL_USERDATA* userData, const double* xloc, double* res, const int* iflag)
{
  DATA *data = userData->data;
  threadData_t *threadData = userData->threadData;
  const int equationIndexes[2] = {1,169};
  int i,j;
  /* iteration variables */
  for (i=0; i<3; i++) {
    if (isinf(xloc[i]) || isnan(xloc[i])) {
      errorStreamPrint(OMC_LOG_NLS, 0, "residualFunc169: Iteration variable `%s` is inf or nan.",
        modelInfoGetEquation(&data->modelData->modelDataXml, 169).vars[i]);
      for (j=0; j<3; j++) {
        res[j] = NAN;
      }
      throwStreamPrintWithEquationIndexes(threadData, omc_dummyFileInfo, equationIndexes, "residualFunc169 failed at time=%.15g.\nFor more information please use -lv LOG_NLS.", data->localData[0]->timeValue);
      return;
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */) = xloc[0];
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) = xloc[1];
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) = xloc[2];
  /* backup outputs */
  /* pre body */
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_142(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_143(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_144(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_145(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_146(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_147(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_148(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_149(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_150(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_151(data, threadData);
  /* local constraints */
  FishRobot_Examples_HydraulicsStep_eqFunction_152(data, threadData);
  /* body */
  res[0] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */) + (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[65]] /* pipeR.port_b.p variable */)) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[64]] /* pipeR.dp variable */);
  threadData->lastEquationSolved = 155;
  res[1] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */);
  threadData->lastEquationSolved = 154;
  res[2] = ((-(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[164]] /* pump.D PARAM */))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */)) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[21]] /* Q_pump variable */) - (((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[167]] /* pump.k_leak PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */)));
  threadData->lastEquationSolved = 153;
  /* restore known outputs */
  threadData->lastEquationSolved = 169;
}

OMC_DISABLE_OPT
void initializeSparsePatternNLS169(NONLINEAR_SYSTEM_DATA* inSysData)
{
  int i=0;
  const int colPtrIndex[1+3] = {0,3,3,3};
  const int rowIndex[9] = {0,1,2,0,1,2,0,1,2};
  /* sparsity pattern available */
  inSysData->isPatternAvailable = TRUE;
  inSysData->sparsePattern = allocSparsePattern(3, 9, 3);
  
  /* write lead index of compressed sparse column */
  memcpy(inSysData->sparsePattern->leadindex, colPtrIndex, (3+1)*sizeof(unsigned int));
  
  for(i=2;i<3+1;++i)
    inSysData->sparsePattern->leadindex[i] += inSysData->sparsePattern->leadindex[i-1];
  
  /* call sparse index */
  memcpy(inSysData->sparsePattern->index, rowIndex, 9*sizeof(unsigned int));
  
  /* write color array */
  /* color 1 with 1 columns */
  const int indices_1[1] = {2};
  for(i=0; i<1; i++)
    inSysData->sparsePattern->colorCols[indices_1[i]] = 1;
  
  /* color 2 with 1 columns */
  const int indices_2[1] = {1};
  for(i=0; i<1; i++)
    inSysData->sparsePattern->colorCols[indices_2[i]] = 2;
  
  /* color 3 with 1 columns */
  const int indices_3[1] = {0};
  for(i=0; i<1; i++)
    inSysData->sparsePattern->colorCols[indices_3[i]] = 3;
}

void freeSparsePatternNLS169(NONLINEAR_SYSTEM_DATA* inSysData)
{
  if (inSysData->isPatternAvailable) {
    freeSparsePattern(inSysData->sparsePattern);
    free(inSysData->sparsePattern);
    inSysData->sparsePattern = NULL;
    inSysData->isPatternAvailable = FALSE;
  }
}
OMC_DISABLE_OPT
void initializeNonlinearPatternNLS169(NONLINEAR_SYSTEM_DATA* inSysData)
{
  int i=0;
  inSysData->nonlinearPattern = (NONLINEAR_PATTERN*) malloc(sizeof(NONLINEAR_PATTERN));
  inSysData->nonlinearPattern->numberOfVars = 3;
  inSysData->nonlinearPattern->numberOfEqns = 3;
  inSysData->nonlinearPattern->numberOfNonlinear = 7;
  inSysData->nonlinearPattern->indexVar = (unsigned int*) malloc((3+1)*sizeof(unsigned int));
  inSysData->nonlinearPattern->indexEqn = (unsigned int*) malloc((3+1)*sizeof(unsigned int));
  inSysData->nonlinearPattern->columns = (unsigned int*) malloc(7*sizeof(unsigned int));
  inSysData->nonlinearPattern->rows = (unsigned int*) malloc(7*sizeof(unsigned int));
  /* initialize and accumulate index vectors */
  const int index_var[1+3] = {0,3,1,3};
  const int index_eqn[1+3] = {0,3,1,3};
  memcpy(inSysData->nonlinearPattern->indexVar, index_var, (3+1)*sizeof(unsigned int));
  memcpy(inSysData->nonlinearPattern->indexEqn, index_eqn, (3+1)*sizeof(unsigned int));
  for(i=2;i<3+1;++i)
    inSysData->nonlinearPattern->indexVar[i] += inSysData->nonlinearPattern->indexVar[i-1];
  for(i=2;i<3+1;++i)
    inSysData->nonlinearPattern->indexEqn[i] += inSysData->nonlinearPattern->indexEqn[i-1];
  /* initialize columns and rows */
  const int columns[7] = {0,1,2,0,0,1,2};
  const int rows[7] = {0,1,2,0,2,0,2};
  memcpy(inSysData->nonlinearPattern->columns, columns, 7*sizeof(unsigned int));
  memcpy(inSysData->nonlinearPattern->rows, rows, 7*sizeof(unsigned int));
}

OMC_DISABLE_OPT
void initializeStaticDataNLS169(DATA* data, threadData_t *threadData, NONLINEAR_SYSTEM_DATA *sysData, modelica_boolean initSparsePattern, modelica_boolean initNonlinearPattern)
{
  int i=0;
  /* static nls data for pipeL.V_flow */
  sysData->nominal[i] = getNominalFromScalarIdx(data->simulationInfo, data->modelData, VAR_KIND_VARIABLE, 57 /* pipeL.V_flow */);
  sysData->min[i]     = getMinFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 57 /* pipeL.V_flow */);
  sysData->max[i++]   = getMaxFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 57 /* pipeL.V_flow */);
  /* static nls data for reliefRL.dp */
  sysData->nominal[i] = getNominalFromScalarIdx(data->simulationInfo, data->modelData, VAR_KIND_VARIABLE, 80 /* reliefRL.dp */);
  sysData->min[i]     = getMinFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 80 /* reliefRL.dp */);
  sysData->max[i++]   = getMaxFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 80 /* reliefRL.dp */);
  /* static nls data for reliefLR.dp */
  sysData->nominal[i] = getNominalFromScalarIdx(data->simulationInfo, data->modelData, VAR_KIND_VARIABLE, 76 /* reliefLR.dp */);
  sysData->min[i]     = getMinFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 76 /* reliefLR.dp */);
  sysData->max[i++]   = getMaxFromScalarIdx(data->simulationInfo, data->modelData, VAR_TYPE_REAL, VAR_KIND_VARIABLE, 76 /* reliefLR.dp */);
  /* initial sparse pattern */
  if (initSparsePattern) {
    initializeSparsePatternNLS169(sysData);
  }
  if (initNonlinearPattern) {
    initializeNonlinearPatternNLS169(sysData);
  }
}

OMC_DISABLE_OPT
void freeStaticDataNLS169(DATA* data, threadData_t *threadData, NONLINEAR_SYSTEM_DATA *sysData)
{
  freeSparsePatternNLS169(sysData);
}

OMC_DISABLE_OPT
void getIterationVarsNLS169(DATA* data, double *array)
{
  array[0] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  array[1] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */);
  array[2] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */);
}

/* Prototypes for the strict sets (Dynamic Tearing) */

/* Global constraints for the casual sets */
/* function initialize non-linear systems */
void FishRobot_Examples_HydraulicsStep_initialNonLinearSystem(int nNonLinearSystems, NONLINEAR_SYSTEM_DATA* nonLinearSystemData)
{
  
  nonLinearSystemData[1].equationIndex = 169;
  nonLinearSystemData[1].size = 3;
  nonLinearSystemData[1].homotopySupport = 0 /* false */;
  nonLinearSystemData[1].mixedSystem = 0 /* false */;
  nonLinearSystemData[1].residualFunc = residualFunc169;
  nonLinearSystemData[1].strictTearingFunctionCall = NULL;
  nonLinearSystemData[1].analyticalJacobianColumn = FishRobot_Examples_HydraulicsStep_functionJacNLSJac1_column;
  nonLinearSystemData[1].initialAnalyticalJacobian = FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianNLSJac1;
  nonLinearSystemData[1].jacobianIndex = 1 /*jacInx*/;
  nonLinearSystemData[1].initializeStaticNLSData = initializeStaticDataNLS169;
  nonLinearSystemData[1].freeStaticNLSData = freeStaticDataNLS169;
  nonLinearSystemData[1].getIterationVars = getIterationVarsNLS169;
  nonLinearSystemData[1].checkConstraints = NULL;
  
  const int tmp_eqn_indices_1[14] = {142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 155, 154, 153};
  nonLinearSystemData[1].eqn_simcode_indices = malloc(14 * sizeof(int));
  memcpy(nonLinearSystemData[1].eqn_simcode_indices, tmp_eqn_indices_1, 14 * sizeof(int));
  nonLinearSystemData[1].torn_plus_residual_size = 14;
  
  
  nonLinearSystemData[0].equationIndex = 67;
  nonLinearSystemData[0].size = 3;
  nonLinearSystemData[0].homotopySupport = 0 /* false */;
  nonLinearSystemData[0].mixedSystem = 0 /* false */;
  nonLinearSystemData[0].residualFunc = residualFunc67;
  nonLinearSystemData[0].strictTearingFunctionCall = NULL;
  nonLinearSystemData[0].analyticalJacobianColumn = FishRobot_Examples_HydraulicsStep_functionJacNLSJac0_column;
  nonLinearSystemData[0].initialAnalyticalJacobian = FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianNLSJac0;
  nonLinearSystemData[0].jacobianIndex = 0 /*jacInx*/;
  nonLinearSystemData[0].initializeStaticNLSData = initializeStaticDataNLS67;
  nonLinearSystemData[0].freeStaticNLSData = freeStaticDataNLS67;
  nonLinearSystemData[0].getIterationVars = getIterationVarsNLS67;
  nonLinearSystemData[0].checkConstraints = NULL;
  
  const int tmp_eqn_indices_0[14] = {40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 53, 52, 51};
  nonLinearSystemData[0].eqn_simcode_indices = malloc(14 * sizeof(int));
  memcpy(nonLinearSystemData[0].eqn_simcode_indices, tmp_eqn_indices_0, 14 * sizeof(int));
  nonLinearSystemData[0].torn_plus_residual_size = 14;
}

#if defined(__cplusplus)
}
#endif
