/* update bound parameters and variable attributes (start, nominal, min, max) */
#include "FishRobot.Examples.HydraulicsStep_model.h"
#if defined(__cplusplus)
extern "C" {
#endif


/*
equation index: 196
type: SIMPLE_ASSIGN
$START.chamberR.V = chamberR.V_prefill
*/
static void FishRobot_Examples_HydraulicsStep_eqFunction_196(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,196};
  ((modelica_real *)((data->modelData->realVarsData[4] /* chamberR.V STATE(1,pipeR.V_flow) */).attribute .start.data))[0] = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[56]] /* chamberR.V_prefill PARAM */);
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[4]] /* chamberR.V STATE(1,pipeR.V_flow) */) = ((modelica_real *)((data->modelData->realVarsData[4] /* chamberR.V STATE(1,pipeR.V_flow) */).attribute .start.data))[0];
  infoStreamPrint(OMC_LOG_INIT_V, 0,
                  "updated start value: %s(start=%g)",
                  data->modelData->realVarsData[4] /* chamberR.V */ .info.name,
                  (modelica_real) (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[4]] /* chamberR.V STATE(1,pipeR.V_flow) */));
  threadData->lastEquationSolved = 196;
}

/*
equation index: 197
type: SIMPLE_ASSIGN
$START.chamberL.V = chamberL.V_prefill
*/
static void FishRobot_Examples_HydraulicsStep_eqFunction_197(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,197};
  ((modelica_real *)((data->modelData->realVarsData[2] /* chamberL.V STATE(1,pipeL.V_flow) */).attribute .start.data))[0] = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[8]] /* chamberL.V_prefill PARAM */);
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* chamberL.V STATE(1,pipeL.V_flow) */) = ((modelica_real *)((data->modelData->realVarsData[2] /* chamberL.V STATE(1,pipeL.V_flow) */).attribute .start.data))[0];
  infoStreamPrint(OMC_LOG_INIT_V, 0,
                  "updated start value: %s(start=%g)",
                  data->modelData->realVarsData[2] /* chamberL.V */ .info.name,
                  (modelica_real) (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* chamberL.V STATE(1,pipeL.V_flow) */));
  threadData->lastEquationSolved = 197;
}
/*
equation index: 198
type: SIMPLE_ASSIGN
motor.friction.phi_rel = if motor.friction.phi_nominal >= 2.220446049250313e-16 then motor.friction.phi_nominal else 1.0
*/
static void FishRobot_Examples_HydraulicsStep_eqFunction_198(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,198};
  if (data->modelData->realVarsData[5] /* motor.friction.phi_rel */ .dimension.numberOfDimensions == 0) {
    put_real_element((((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[132]] /* motor.friction.phi_nominal PARAM */) >= 2.220446049250313e-16)?(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[132]] /* motor.friction.phi_nominal PARAM */):1.0), 0, &data->modelData->realVarsData[5] /* motor.friction.phi_rel */ .attribute.nominal);
  } else {
    throwStreamPrint(NULL, "Not yet implemented for array nominal.");
  }

  if (omc_useStream[OMC_LOG_INIT_V]) {
    char nominal_buffer[2048];
    real_vector_to_string(&data->modelData->realVarsData[5] /* motor.friction.phi_rel */ .attribute.nominal, data->modelData->realVarsData[5] /* motor.friction.phi_rel */ .dimension.numberOfDimensions == 0, nominal_buffer, 2048);
    infoStreamPrint(OMC_LOG_INIT_V, 0, "%s(nominal=%s)",
      data->modelData->realVarsData[5] /* motor.friction.phi_rel */ .info.name,
      nominal_buffer);
  }
  threadData->lastEquationSolved = 198;
}

OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_updateBoundVariableAttributes(DATA *data, threadData_t *threadData)
{
  /* min ******************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating min-values");
  messageClose(OMC_LOG_INIT);
  
  /* max ******************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating max-values");
  messageClose(OMC_LOG_INIT);
  
  /* nominal **************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating nominal-values");
  FishRobot_Examples_HydraulicsStep_eqFunction_198(data, threadData);
  messageClose(OMC_LOG_INIT);
  
  /* start ****************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating primary start-values");
  FishRobot_Examples_HydraulicsStep_eqFunction_196(data, threadData);
  FishRobot_Examples_HydraulicsStep_eqFunction_197(data, threadData);
  messageClose(OMC_LOG_INIT);
  
  return 0;
}

void FishRobot_Examples_HydraulicsStep_updateBoundParameters_0(DATA *data, threadData_t *threadData);

/*
equation index: 199
type: SIMPLE_ASSIGN
command.shiftTime = command.startTime
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_199(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,199};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[106]] /* command.shiftTime PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[107]] /* command.startTime PARAM */);
  threadData->lastEquationSolved = 199;
}

/*
equation index: 200
type: SIMPLE_ASSIGN
command.tableID = Modelica.Blocks.Types.ExternalCombiTimeTable.constructor("NoName", "NoName", command.table, command.startTime, command.columns, Modelica.Blocks.Types.Smoothness.LinearSegments, Modelica.Blocks.Types.Extrapolation.LastTwoPoints, command.shiftTime, command.timeEvents, false, command.delimiter, command.nHeaderLines)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_200(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,200};
  real_array tmp0;
  integer_array tmp1;
  real_array_create(&tmp0, ((modelica_real*)&((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[112]] /* command.table[1,1] PARAM */))), 2, (_index_t)6, (_index_t)2);
  integer_array_create(&tmp1, ((modelica_integer*)&((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[12]] /* command.columns[1] PARAM */))), 1, (_index_t)1);
  (data->simulationInfo->extObjs[2]) = omc_Modelica_Blocks_Types_ExternalCombiTimeTable_constructor(threadData, _OMC_LIT1, _OMC_LIT1, tmp0, (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[107]] /* command.startTime PARAM */), tmp1, 1, 2, (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[106]] /* command.shiftTime PARAM */), (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[17]] /* command.timeEvents PARAM */), 0 /* false */, (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[10]] /* command.delimiter PARAM */), (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[14]] /* command.nHeaderLines PARAM */));
  threadData->lastEquationSolved = 200;
}

/*
equation index: 201
type: SIMPLE_ASSIGN
chamberL.pV.table[1,1] = chamberL.table[1,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_201(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,201};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[9]] /* chamberL.pV.table[1,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[34]] /* chamberL.table[1,1] PARAM */);
  threadData->lastEquationSolved = 201;
}

/*
equation index: 202
type: SIMPLE_ASSIGN
chamberL.pV.table[1,2] = chamberL.table[1,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_202(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,202};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[10]] /* chamberL.pV.table[1,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[35]] /* chamberL.table[1,2] PARAM */);
  threadData->lastEquationSolved = 202;
}

/*
equation index: 203
type: SIMPLE_ASSIGN
chamberL.pV.table[2,1] = chamberL.table[2,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_203(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,203};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[11]] /* chamberL.pV.table[2,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[36]] /* chamberL.table[2,1] PARAM */);
  threadData->lastEquationSolved = 203;
}

/*
equation index: 204
type: SIMPLE_ASSIGN
chamberL.pV.table[2,2] = chamberL.table[2,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_204(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,204};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[12]] /* chamberL.pV.table[2,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[37]] /* chamberL.table[2,2] PARAM */);
  threadData->lastEquationSolved = 204;
}

/*
equation index: 205
type: SIMPLE_ASSIGN
chamberL.pV.table[3,1] = chamberL.table[3,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_205(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,205};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* chamberL.pV.table[3,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[38]] /* chamberL.table[3,1] PARAM */);
  threadData->lastEquationSolved = 205;
}

/*
equation index: 206
type: SIMPLE_ASSIGN
chamberL.pV.table[3,2] = chamberL.table[3,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_206(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,206};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* chamberL.pV.table[3,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[39]] /* chamberL.table[3,2] PARAM */);
  threadData->lastEquationSolved = 206;
}

/*
equation index: 207
type: SIMPLE_ASSIGN
chamberL.pV.table[4,1] = chamberL.table[4,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_207(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,207};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[15]] /* chamberL.pV.table[4,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[40]] /* chamberL.table[4,1] PARAM */);
  threadData->lastEquationSolved = 207;
}

/*
equation index: 208
type: SIMPLE_ASSIGN
chamberL.pV.table[4,2] = chamberL.table[4,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_208(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,208};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[16]] /* chamberL.pV.table[4,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[41]] /* chamberL.table[4,2] PARAM */);
  threadData->lastEquationSolved = 208;
}

/*
equation index: 209
type: SIMPLE_ASSIGN
chamberL.pV.table[5,1] = chamberL.table[5,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_209(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,209};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[17]] /* chamberL.pV.table[5,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[42]] /* chamberL.table[5,1] PARAM */);
  threadData->lastEquationSolved = 209;
}

/*
equation index: 210
type: SIMPLE_ASSIGN
chamberL.pV.table[5,2] = chamberL.table[5,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_210(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,210};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[18]] /* chamberL.pV.table[5,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[43]] /* chamberL.table[5,2] PARAM */);
  threadData->lastEquationSolved = 210;
}

/*
equation index: 211
type: SIMPLE_ASSIGN
chamberL.pV.table[6,1] = chamberL.table[6,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_211(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,211};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[19]] /* chamberL.pV.table[6,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[44]] /* chamberL.table[6,1] PARAM */);
  threadData->lastEquationSolved = 211;
}

/*
equation index: 212
type: SIMPLE_ASSIGN
chamberL.pV.table[6,2] = chamberL.table[6,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_212(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,212};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[20]] /* chamberL.pV.table[6,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[45]] /* chamberL.table[6,2] PARAM */);
  threadData->lastEquationSolved = 212;
}

/*
equation index: 213
type: SIMPLE_ASSIGN
chamberL.pV.table[7,1] = chamberL.table[7,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_213(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,213};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[21]] /* chamberL.pV.table[7,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[46]] /* chamberL.table[7,1] PARAM */);
  threadData->lastEquationSolved = 213;
}

/*
equation index: 214
type: SIMPLE_ASSIGN
chamberL.pV.table[7,2] = chamberL.table[7,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_214(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,214};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[22]] /* chamberL.pV.table[7,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[47]] /* chamberL.table[7,2] PARAM */);
  threadData->lastEquationSolved = 214;
}

/*
equation index: 215
type: SIMPLE_ASSIGN
chamberL.pV.table[8,1] = chamberL.table[8,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_215(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,215};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[23]] /* chamberL.pV.table[8,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[48]] /* chamberL.table[8,1] PARAM */);
  threadData->lastEquationSolved = 215;
}

/*
equation index: 216
type: SIMPLE_ASSIGN
chamberL.pV.table[8,2] = chamberL.table[8,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_216(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,216};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[24]] /* chamberL.pV.table[8,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[49]] /* chamberL.table[8,2] PARAM */);
  threadData->lastEquationSolved = 216;
}

/*
equation index: 217
type: SIMPLE_ASSIGN
chamberL.pV.table[9,1] = chamberL.table[9,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_217(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,217};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[25]] /* chamberL.pV.table[9,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[50]] /* chamberL.table[9,1] PARAM */);
  threadData->lastEquationSolved = 217;
}

/*
equation index: 218
type: SIMPLE_ASSIGN
chamberL.pV.table[9,2] = chamberL.table[9,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_218(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,218};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[26]] /* chamberL.pV.table[9,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[51]] /* chamberL.table[9,2] PARAM */);
  threadData->lastEquationSolved = 218;
}

/*
equation index: 219
type: SIMPLE_ASSIGN
chamberL.pV.table[10,1] = chamberL.table[10,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_219(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,219};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[27]] /* chamberL.pV.table[10,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[52]] /* chamberL.table[10,1] PARAM */);
  threadData->lastEquationSolved = 219;
}

/*
equation index: 220
type: SIMPLE_ASSIGN
chamberL.pV.table[10,2] = chamberL.table[10,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_220(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,220};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[28]] /* chamberL.pV.table[10,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[53]] /* chamberL.table[10,2] PARAM */);
  threadData->lastEquationSolved = 220;
}

/*
equation index: 221
type: SIMPLE_ASSIGN
chamberL.pV.table[11,1] = chamberL.table[11,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_221(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,221};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[29]] /* chamberL.pV.table[11,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[54]] /* chamberL.table[11,1] PARAM */);
  threadData->lastEquationSolved = 221;
}

/*
equation index: 222
type: SIMPLE_ASSIGN
chamberL.pV.table[11,2] = chamberL.table[11,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_222(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,222};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[30]] /* chamberL.pV.table[11,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[55]] /* chamberL.table[11,2] PARAM */);
  threadData->lastEquationSolved = 222;
}

/*
equation index: 223
type: SIMPLE_ASSIGN
chamberL.pV.delimiter = ","
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_223(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,223};
  (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[1]] /* chamberL.pV.delimiter PARAM */) = _OMC_LIT0;
  threadData->lastEquationSolved = 223;
}

/*
equation index: 224
type: SIMPLE_ASSIGN
chamberL.pV.nHeaderLines = chamberL.nHeaderLines
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_224(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,224};
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[3]] /* chamberL.pV.nHeaderLines PARAM */) = (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[0]] /* chamberL.nHeaderLines PARAM */);
  threadData->lastEquationSolved = 224;
}

/*
equation index: 225
type: SIMPLE_ASSIGN
chamberL.pV.tableID = Modelica.Blocks.Types.ExternalCombiTable1D.constructor("NoName", "NoName", chamberL.pV.table, {2}, Modelica.Blocks.Types.Smoothness.MonotoneContinuousDerivative1, Modelica.Blocks.Types.Extrapolation.LastTwoPoints, false, chamberL.pV.delimiter, chamberL.pV.nHeaderLines)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_225(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,225};
  real_array tmp2;
  real_array_create(&tmp2, ((modelica_real*)&((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[9]] /* chamberL.pV.table[1,1] PARAM */))), 2, (_index_t)11, (_index_t)2);
  (data->simulationInfo->extObjs[0]) = omc_Modelica_Blocks_Types_ExternalCombiTable1D_constructor(threadData, _OMC_LIT1, _OMC_LIT1, tmp2, _OMC_LIT2, 4, 2, 0 /* false */, (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[1]] /* chamberL.pV.delimiter PARAM */), (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[3]] /* chamberL.pV.nHeaderLines PARAM */));
  threadData->lastEquationSolved = 225;
}

/*
equation index: 226
type: SIMPLE_ASSIGN
chamberR.pV.table[1,1] = chamberR.table[1,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_226(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,226};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[57]] /* chamberR.pV.table[1,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[82]] /* chamberR.table[1,1] PARAM */);
  threadData->lastEquationSolved = 226;
}

/*
equation index: 227
type: SIMPLE_ASSIGN
chamberR.pV.table[1,2] = chamberR.table[1,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_227(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,227};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[58]] /* chamberR.pV.table[1,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[83]] /* chamberR.table[1,2] PARAM */);
  threadData->lastEquationSolved = 227;
}

/*
equation index: 228
type: SIMPLE_ASSIGN
chamberR.pV.table[2,1] = chamberR.table[2,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_228(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,228};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[59]] /* chamberR.pV.table[2,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[84]] /* chamberR.table[2,1] PARAM */);
  threadData->lastEquationSolved = 228;
}

/*
equation index: 229
type: SIMPLE_ASSIGN
chamberR.pV.table[2,2] = chamberR.table[2,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_229(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,229};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[60]] /* chamberR.pV.table[2,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[85]] /* chamberR.table[2,2] PARAM */);
  threadData->lastEquationSolved = 229;
}

/*
equation index: 230
type: SIMPLE_ASSIGN
chamberR.pV.table[3,1] = chamberR.table[3,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_230(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,230};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[61]] /* chamberR.pV.table[3,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[86]] /* chamberR.table[3,1] PARAM */);
  threadData->lastEquationSolved = 230;
}

/*
equation index: 231
type: SIMPLE_ASSIGN
chamberR.pV.table[3,2] = chamberR.table[3,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_231(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,231};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[62]] /* chamberR.pV.table[3,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[87]] /* chamberR.table[3,2] PARAM */);
  threadData->lastEquationSolved = 231;
}

/*
equation index: 232
type: SIMPLE_ASSIGN
chamberR.pV.table[4,1] = chamberR.table[4,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_232(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,232};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[63]] /* chamberR.pV.table[4,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[88]] /* chamberR.table[4,1] PARAM */);
  threadData->lastEquationSolved = 232;
}

/*
equation index: 233
type: SIMPLE_ASSIGN
chamberR.pV.table[4,2] = chamberR.table[4,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_233(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,233};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[64]] /* chamberR.pV.table[4,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[89]] /* chamberR.table[4,2] PARAM */);
  threadData->lastEquationSolved = 233;
}

/*
equation index: 234
type: SIMPLE_ASSIGN
chamberR.pV.table[5,1] = chamberR.table[5,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_234(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,234};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[65]] /* chamberR.pV.table[5,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[90]] /* chamberR.table[5,1] PARAM */);
  threadData->lastEquationSolved = 234;
}

/*
equation index: 235
type: SIMPLE_ASSIGN
chamberR.pV.table[5,2] = chamberR.table[5,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_235(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,235};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[66]] /* chamberR.pV.table[5,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[91]] /* chamberR.table[5,2] PARAM */);
  threadData->lastEquationSolved = 235;
}

/*
equation index: 236
type: SIMPLE_ASSIGN
chamberR.pV.table[6,1] = chamberR.table[6,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_236(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,236};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[67]] /* chamberR.pV.table[6,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[92]] /* chamberR.table[6,1] PARAM */);
  threadData->lastEquationSolved = 236;
}

/*
equation index: 237
type: SIMPLE_ASSIGN
chamberR.pV.table[6,2] = chamberR.table[6,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_237(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,237};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[68]] /* chamberR.pV.table[6,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[93]] /* chamberR.table[6,2] PARAM */);
  threadData->lastEquationSolved = 237;
}

/*
equation index: 238
type: SIMPLE_ASSIGN
chamberR.pV.table[7,1] = chamberR.table[7,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_238(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,238};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[69]] /* chamberR.pV.table[7,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[94]] /* chamberR.table[7,1] PARAM */);
  threadData->lastEquationSolved = 238;
}

/*
equation index: 239
type: SIMPLE_ASSIGN
chamberR.pV.table[7,2] = chamberR.table[7,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_239(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,239};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[70]] /* chamberR.pV.table[7,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[95]] /* chamberR.table[7,2] PARAM */);
  threadData->lastEquationSolved = 239;
}

/*
equation index: 240
type: SIMPLE_ASSIGN
chamberR.pV.table[8,1] = chamberR.table[8,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_240(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,240};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[71]] /* chamberR.pV.table[8,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[96]] /* chamberR.table[8,1] PARAM */);
  threadData->lastEquationSolved = 240;
}

/*
equation index: 241
type: SIMPLE_ASSIGN
chamberR.pV.table[8,2] = chamberR.table[8,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_241(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,241};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[72]] /* chamberR.pV.table[8,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[97]] /* chamberR.table[8,2] PARAM */);
  threadData->lastEquationSolved = 241;
}

/*
equation index: 242
type: SIMPLE_ASSIGN
chamberR.pV.table[9,1] = chamberR.table[9,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_242(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,242};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[73]] /* chamberR.pV.table[9,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[98]] /* chamberR.table[9,1] PARAM */);
  threadData->lastEquationSolved = 242;
}

/*
equation index: 243
type: SIMPLE_ASSIGN
chamberR.pV.table[9,2] = chamberR.table[9,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_243(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,243};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[74]] /* chamberR.pV.table[9,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[99]] /* chamberR.table[9,2] PARAM */);
  threadData->lastEquationSolved = 243;
}

/*
equation index: 244
type: SIMPLE_ASSIGN
chamberR.pV.table[10,1] = chamberR.table[10,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_244(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,244};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[75]] /* chamberR.pV.table[10,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[100]] /* chamberR.table[10,1] PARAM */);
  threadData->lastEquationSolved = 244;
}

/*
equation index: 245
type: SIMPLE_ASSIGN
chamberR.pV.table[10,2] = chamberR.table[10,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_245(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,245};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[76]] /* chamberR.pV.table[10,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[101]] /* chamberR.table[10,2] PARAM */);
  threadData->lastEquationSolved = 245;
}

/*
equation index: 246
type: SIMPLE_ASSIGN
chamberR.pV.table[11,1] = chamberR.table[11,1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_246(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,246};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[77]] /* chamberR.pV.table[11,1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[102]] /* chamberR.table[11,1] PARAM */);
  threadData->lastEquationSolved = 246;
}

/*
equation index: 247
type: SIMPLE_ASSIGN
chamberR.pV.table[11,2] = chamberR.table[11,2]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_247(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,247};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[78]] /* chamberR.pV.table[11,2] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[103]] /* chamberR.table[11,2] PARAM */);
  threadData->lastEquationSolved = 247;
}

/*
equation index: 248
type: SIMPLE_ASSIGN
chamberR.pV.delimiter = ","
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_248(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,248};
  (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[6]] /* chamberR.pV.delimiter PARAM */) = _OMC_LIT0;
  threadData->lastEquationSolved = 248;
}

/*
equation index: 249
type: SIMPLE_ASSIGN
chamberR.pV.nHeaderLines = chamberR.nHeaderLines
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_249(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,249};
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[9]] /* chamberR.pV.nHeaderLines PARAM */) = (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[6]] /* chamberR.nHeaderLines PARAM */);
  threadData->lastEquationSolved = 249;
}

/*
equation index: 250
type: SIMPLE_ASSIGN
chamberR.pV.tableID = Modelica.Blocks.Types.ExternalCombiTable1D.constructor("NoName", "NoName", chamberR.pV.table, {2}, Modelica.Blocks.Types.Smoothness.MonotoneContinuousDerivative1, Modelica.Blocks.Types.Extrapolation.LastTwoPoints, false, chamberR.pV.delimiter, chamberR.pV.nHeaderLines)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_250(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,250};
  real_array tmp3;
  real_array_create(&tmp3, ((modelica_real*)&((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[57]] /* chamberR.pV.table[1,1] PARAM */))), 2, (_index_t)11, (_index_t)2);
  (data->simulationInfo->extObjs[1]) = omc_Modelica_Blocks_Types_ExternalCombiTable1D_constructor(threadData, _OMC_LIT1, _OMC_LIT1, tmp3, _OMC_LIT2, 4, 2, 0 /* false */, (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[6]] /* chamberR.pV.delimiter PARAM */), (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[9]] /* chamberR.pV.nHeaderLines PARAM */));
  threadData->lastEquationSolved = 250;
}

/*
equation index: 251
type: SIMPLE_ASSIGN
reliefRL.G_open = reliefRL.V_flow_nominal / reliefRL.dp_open
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_251(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,251};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[176]] /* reliefRL.G_open PARAM */) = DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[177]] /* reliefRL.V_flow_nominal PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[178]] /* reliefRL.dp_open PARAM */),"reliefRL.dp_open",equationIndexes);
  threadData->lastEquationSolved = 251;
}

/*
equation index: 252
type: SIMPLE_ASSIGN
reliefLR.G_open = reliefLR.V_flow_nominal / reliefLR.dp_open
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_252(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,252};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[170]] /* reliefLR.G_open PARAM */) = DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[171]] /* reliefLR.V_flow_nominal PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[172]] /* reliefLR.dp_open PARAM */),"reliefLR.dp_open",equationIndexes);
  threadData->lastEquationSolved = 252;
}

/*
equation index: 254
type: SIMPLE_ASSIGN
chamberR.pV.u_max = Modelica.Blocks.Tables.Internal.getTable1DAbscissaUmax(chamberR.pV.tableID)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_254(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,254};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[79]] /* chamberR.pV.u_max PARAM */) = omc_Modelica_Blocks_Tables_Internal_getTable1DAbscissaUmax(threadData, (data->simulationInfo->extObjs[1]));
  threadData->lastEquationSolved = 254;
}

/*
equation index: 255
type: SIMPLE_ASSIGN
chamberR.pV.u_min = Modelica.Blocks.Tables.Internal.getTable1DAbscissaUmin(chamberR.pV.tableID)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_255(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,255};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[80]] /* chamberR.pV.u_min PARAM */) = omc_Modelica_Blocks_Tables_Internal_getTable1DAbscissaUmin(threadData, (data->simulationInfo->extObjs[1]));
  threadData->lastEquationSolved = 255;
}

/*
equation index: 261
type: SIMPLE_ASSIGN
chamberR.pV.fileName = chamberR.fileName
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_261(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,261};
  (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[7]] /* chamberR.pV.fileName PARAM */) = (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[5]] /* chamberR.fileName PARAM */);
  threadData->lastEquationSolved = 261;
}

/*
equation index: 262
type: SIMPLE_ASSIGN
chamberR.pV.tableName = chamberR.tableName
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_262(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,262};
  (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[8]] /* chamberR.pV.tableName PARAM */) = (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[9]] /* chamberR.tableName PARAM */);
  threadData->lastEquationSolved = 262;
}

/*
equation index: 266
type: SIMPLE_ASSIGN
chamberR.V_prefill = V_prefill
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_266(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,266};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[56]] /* chamberR.V_prefill PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* V_prefill PARAM */);
  threadData->lastEquationSolved = 266;
}

/*
equation index: 267
type: SIMPLE_ASSIGN
chamberR.p_ambient = p_ambient
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_267(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,267};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[81]] /* chamberR.p_ambient PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[141]] /* p_ambient PARAM */);
  threadData->lastEquationSolved = 267;
}

/*
equation index: 269
type: SIMPLE_ASSIGN
chamberL.pV.u_max = Modelica.Blocks.Tables.Internal.getTable1DAbscissaUmax(chamberL.pV.tableID)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_269(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,269};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[31]] /* chamberL.pV.u_max PARAM */) = omc_Modelica_Blocks_Tables_Internal_getTable1DAbscissaUmax(threadData, (data->simulationInfo->extObjs[0]));
  threadData->lastEquationSolved = 269;
}

/*
equation index: 270
type: SIMPLE_ASSIGN
chamberL.pV.u_min = Modelica.Blocks.Tables.Internal.getTable1DAbscissaUmin(chamberL.pV.tableID)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_270(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,270};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[32]] /* chamberL.pV.u_min PARAM */) = omc_Modelica_Blocks_Tables_Internal_getTable1DAbscissaUmin(threadData, (data->simulationInfo->extObjs[0]));
  threadData->lastEquationSolved = 270;
}

/*
equation index: 276
type: SIMPLE_ASSIGN
chamberL.pV.fileName = chamberL.fileName
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_276(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,276};
  (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[2]] /* chamberL.pV.fileName PARAM */) = (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[0]] /* chamberL.fileName PARAM */);
  threadData->lastEquationSolved = 276;
}

/*
equation index: 277
type: SIMPLE_ASSIGN
chamberL.pV.tableName = chamberL.tableName
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_277(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,277};
  (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[3]] /* chamberL.pV.tableName PARAM */) = (data->simulationInfo->stringParameter[data->simulationInfo->stringParamsIndex[4]] /* chamberL.tableName PARAM */);
  threadData->lastEquationSolved = 277;
}

/*
equation index: 281
type: SIMPLE_ASSIGN
chamberL.V_prefill = V_prefill
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_281(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,281};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[8]] /* chamberL.V_prefill PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* V_prefill PARAM */);
  threadData->lastEquationSolved = 281;
}

/*
equation index: 282
type: SIMPLE_ASSIGN
chamberL.p_ambient = p_ambient
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_282(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,282};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[33]] /* chamberL.p_ambient PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[141]] /* p_ambient PARAM */);
  threadData->lastEquationSolved = 282;
}

/*
equation index: 283
type: SIMPLE_ASSIGN
pipeR.A = 0.7853981633974483 * pipeR.d ^ 2.0
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_283(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,283};
  modelica_real tmp4;
  tmp4 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[159]] /* pipeR.d PARAM */);
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[153]] /* pipeR.A PARAM */) = (0.7853981633974483) * ((tmp4 * tmp4));
  threadData->lastEquationSolved = 283;
}

/*
equation index: 284
type: SIMPLE_ASSIGN
pipeR.L_inert = pipeR.rho * pipeR.l / pipeR.A
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_284(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,284};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[154]] /* pipeR.L_inert PARAM */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[162]] /* pipeR.rho PARAM */)) * (DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[160]] /* pipeR.l PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[153]] /* pipeR.A PARAM */),"pipeR.A",equationIndexes));
  threadData->lastEquationSolved = 284;
}

/*
equation index: 285
type: SIMPLE_ASSIGN
pipeR.R_turb = 0.5 * pipeR.zeta * pipeR.rho / pipeR.A ^ 2.0
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_285(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,285};
  modelica_real tmp5;
  tmp5 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[153]] /* pipeR.A PARAM */);
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[156]] /* pipeR.R_turb PARAM */) = (0.5) * (((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[163]] /* pipeR.zeta PARAM */)) * (DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[162]] /* pipeR.rho PARAM */),(tmp5 * tmp5),"pipeR.A ^ 2.0",equationIndexes)));
  threadData->lastEquationSolved = 285;
}

/*
equation index: 286
type: SIMPLE_ASSIGN
pipeR.R_lam = 128.0 * pipeR.mu * pipeR.l / (3.141592653589793 * pipeR.d ^ 4.0)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_286(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,286};
  modelica_real tmp6;
  tmp6 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[159]] /* pipeR.d PARAM */);
  tmp6 *= tmp6;
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[155]] /* pipeR.R_lam PARAM */) = DIVISION_SIM(((128.0) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[161]] /* pipeR.mu PARAM */))) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[160]] /* pipeR.l PARAM */)),(3.141592653589793) * ((tmp6 * tmp6)),"3.141592653589793 * pipeR.d ^ 4.0",equationIndexes);
  threadData->lastEquationSolved = 286;
}

/*
equation index: 288
type: SIMPLE_ASSIGN
pipeL.A = 0.7853981633974483 * pipeL.d ^ 2.0
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_288(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,288};
  modelica_real tmp7;
  tmp7 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[148]] /* pipeL.d PARAM */);
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[142]] /* pipeL.A PARAM */) = (0.7853981633974483) * ((tmp7 * tmp7));
  threadData->lastEquationSolved = 288;
}

/*
equation index: 289
type: SIMPLE_ASSIGN
pipeL.L_inert = pipeL.rho * pipeL.l / pipeL.A
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_289(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,289};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[143]] /* pipeL.L_inert PARAM */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[151]] /* pipeL.rho PARAM */)) * (DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[149]] /* pipeL.l PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[142]] /* pipeL.A PARAM */),"pipeL.A",equationIndexes));
  threadData->lastEquationSolved = 289;
}

/*
equation index: 290
type: SIMPLE_ASSIGN
pipeL.R_turb = 0.5 * pipeL.zeta * pipeL.rho / pipeL.A ^ 2.0
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_290(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,290};
  modelica_real tmp8;
  tmp8 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[142]] /* pipeL.A PARAM */);
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[145]] /* pipeL.R_turb PARAM */) = (0.5) * (((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[152]] /* pipeL.zeta PARAM */)) * (DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[151]] /* pipeL.rho PARAM */),(tmp8 * tmp8),"pipeL.A ^ 2.0",equationIndexes)));
  threadData->lastEquationSolved = 290;
}

/*
equation index: 291
type: SIMPLE_ASSIGN
pipeL.R_lam = 128.0 * pipeL.mu * pipeL.l / (3.141592653589793 * pipeL.d ^ 4.0)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_291(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,291};
  modelica_real tmp9;
  tmp9 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[148]] /* pipeL.d PARAM */);
  tmp9 *= tmp9;
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[144]] /* pipeL.R_lam PARAM */) = DIVISION_SIM(((128.0) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[150]] /* pipeL.mu PARAM */))) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[149]] /* pipeL.l PARAM */)),(3.141592653589793) * ((tmp9 * tmp9)),"3.141592653589793 * pipeL.d ^ 4.0",equationIndexes);
  threadData->lastEquationSolved = 291;
}

/*
equation index: 293
type: SIMPLE_ASSIGN
pump.D = 0.15915494309189535 * pump.D_rev
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_293(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,293};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[164]] /* pump.D PARAM */) = (0.15915494309189535) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[165]] /* pump.D_rev PARAM */));
  threadData->lastEquationSolved = 293;
}

/*
equation index: 295
type: SIMPLE_ASSIGN
command.p_offset[1] = command.offset[1]
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_295(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,295};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[105]] /* command.p_offset[1] PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[104]] /* command.offset[1] PARAM */);
  threadData->lastEquationSolved = 295;
}

/*
equation index: 296
type: SIMPLE_ASSIGN
command.t_maxScaled = Modelica.Blocks.Tables.Internal.getTimeTableTmax(command.tableID)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_296(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,296};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[109]] /* command.t_maxScaled PARAM */) = omc_Modelica_Blocks_Tables_Internal_getTimeTableTmax(threadData, (data->simulationInfo->extObjs[2]));
  threadData->lastEquationSolved = 296;
}

/*
equation index: 297
type: SIMPLE_ASSIGN
command.t_minScaled = Modelica.Blocks.Tables.Internal.getTimeTableTmin(command.tableID)
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_297(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,297};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[111]] /* command.t_minScaled PARAM */) = omc_Modelica_Blocks_Tables_Internal_getTimeTableTmin(threadData, (data->simulationInfo->extObjs[2]));
  threadData->lastEquationSolved = 297;
}

/*
equation index: 298
type: SIMPLE_ASSIGN
command.t_max = command.t_maxScaled
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_298(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,298};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[108]] /* command.t_max PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[109]] /* command.t_maxScaled PARAM */);
  threadData->lastEquationSolved = 298;
}

/*
equation index: 299
type: SIMPLE_ASSIGN
command.t_min = command.t_minScaled
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_299(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,299};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[110]] /* command.t_min PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[111]] /* command.t_minScaled PARAM */);
  threadData->lastEquationSolved = 299;
}

/*
equation index: 307
type: SIMPLE_ASSIGN
motor.friction.d = motor.b
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_307(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,307};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[131]] /* motor.friction.d PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[128]] /* motor.b PARAM */);
  threadData->lastEquationSolved = 307;
}

/*
equation index: 310
type: SIMPLE_ASSIGN
motor.rotor.J = motor.J
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_310(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,310};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[140]] /* motor.rotor.J PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[125]] /* motor.J PARAM */);
  threadData->lastEquationSolved = 310;
}

/*
equation index: 312
type: SIMPLE_ASSIGN
motor.emf.k = motor.k
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_312(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,312};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[130]] /* motor.emf.k PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[135]] /* motor.k PARAM */);
  threadData->lastEquationSolved = 312;
}

/*
equation index: 314
type: SIMPLE_ASSIGN
motor.inductor.L = motor.L
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_314(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,314};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[134]] /* motor.inductor.L PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[126]] /* motor.L PARAM */);
  threadData->lastEquationSolved = 314;
}

/*
equation index: 315
type: SIMPLE_ASSIGN
motor.resistor.T = motor.resistor.T_ref
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_315(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,315};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[137]] /* motor.resistor.T PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[138]] /* motor.resistor.T_ref PARAM */);
  threadData->lastEquationSolved = 315;
}

/*
equation index: 317
type: SIMPLE_ASSIGN
motor.resistor.R = motor.R
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_317(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,317};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[136]] /* motor.resistor.R PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[127]] /* motor.R PARAM */);
  threadData->lastEquationSolved = 317;
}

/*
equation index: 319
type: SIMPLE_ASSIGN
battery.rInt.T = battery.rInt.T_ref
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_319(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,319};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* battery.rInt.T PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* battery.rInt.T_ref PARAM */);
  threadData->lastEquationSolved = 319;
}

/*
equation index: 322
type: SIMPLE_ASSIGN
battery.rInt.R = battery.R_int
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_322(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,322};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[4]] /* battery.rInt.R PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* battery.R_int PARAM */);
  threadData->lastEquationSolved = 322;
}

/*
equation index: 323
type: SIMPLE_ASSIGN
battery.cell.V = battery.U_nom
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_323(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,323};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[3]] /* battery.cell.V PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* battery.U_nom PARAM */);
  threadData->lastEquationSolved = 323;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_92(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_2(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_1(DATA *data, threadData_t *threadData);


/*
equation index: 327
type: ALGORITHM

  assert(command.timeEvents >= Modelica.Blocks.Types.TimeEvents.Always and command.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents, "Variable violating min/max constraint: Modelica.Blocks.Types.TimeEvents.Always <= command.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents, has value: " + String(command.timeEvents, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_327(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,327};
  modelica_boolean tmp10;
  modelica_boolean tmp11;
  static const MMC_DEFSTRINGLIT(tmp12,162,"Variable violating min/max constraint: Modelica.Blocks.Types.TimeEvents.Always <= command.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents, has value: ");
  modelica_string tmp13;
  modelica_metatype tmpMeta14;
  static int tmp15 = 0;
  if(!tmp15)
  {
    tmp10 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[17]] /* command.timeEvents PARAM */),1);
    tmp11 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[17]] /* command.timeEvents PARAM */),3);
    if(!(tmp10 && tmp11))
    {
      tmp13 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[17]] /* command.timeEvents PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta14 = stringAppend(MMC_REFSTRINGLIT(tmp12),tmp13);
      {
        const char* assert_cond = "(command.timeEvents >= Modelica.Blocks.Types.TimeEvents.Always and command.timeEvents <= Modelica.Blocks.Types.TimeEvents.NoTimeEvents)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Sources.mo",1638,5,1640,131,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta14));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Sources.mo",1638,5,1640,131,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta14));
        }
      }
      tmp15 = 1;
    }
  }
  threadData->lastEquationSolved = 327;
}

/*
equation index: 328
type: ALGORITHM

  assert(chamberR.pV.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and chamberR.pV.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, "Variable violating min/max constraint: Modelica.Blocks.Types.Extrapolation.HoldLastPoint <= chamberR.pV.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, has value: " + String(chamberR.pV.extrapolation, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_328(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,328};
  modelica_boolean tmp16;
  modelica_boolean tmp17;
  static const MMC_DEFSTRINGLIT(tmp18,185,"Variable violating min/max constraint: Modelica.Blocks.Types.Extrapolation.HoldLastPoint <= chamberR.pV.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, has value: ");
  modelica_string tmp19;
  modelica_metatype tmpMeta20;
  static int tmp21 = 0;
  if(!tmp21)
  {
    tmp16 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[8]] /* chamberR.pV.extrapolation PARAM */),1);
    tmp17 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[8]] /* chamberR.pV.extrapolation PARAM */),4);
    if(!(tmp16 && tmp17))
    {
      tmp19 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[8]] /* chamberR.pV.extrapolation PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta20 = stringAppend(MMC_REFSTRINGLIT(tmp18),tmp19);
      {
        const char* assert_cond = "(chamberR.pV.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and chamberR.pV.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Tables.mo",39,5,41,61,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta20));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Tables.mo",39,5,41,61,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta20));
        }
      }
      tmp21 = 1;
    }
  }
  threadData->lastEquationSolved = 328;
}

/*
equation index: 329
type: ALGORITHM

  assert(chamberR.pV.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and chamberR.pV.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, "Variable violating min/max constraint: Modelica.Blocks.Types.Smoothness.LinearSegments <= chamberR.pV.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, has value: " + String(chamberR.pV.smoothness, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_329(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,329};
  modelica_boolean tmp22;
  modelica_boolean tmp23;
  static const MMC_DEFSTRINGLIT(tmp24,190,"Variable violating min/max constraint: Modelica.Blocks.Types.Smoothness.LinearSegments <= chamberR.pV.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, has value: ");
  modelica_string tmp25;
  modelica_metatype tmpMeta26;
  static int tmp27 = 0;
  if(!tmp27)
  {
    tmp22 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[11]] /* chamberR.pV.smoothness PARAM */),1);
    tmp23 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[11]] /* chamberR.pV.smoothness PARAM */),6);
    if(!(tmp22 && tmp23))
    {
      tmp25 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[11]] /* chamberR.pV.smoothness PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta26 = stringAppend(MMC_REFSTRINGLIT(tmp24),tmp25);
      {
        const char* assert_cond = "(chamberR.pV.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and chamberR.pV.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Tables.mo",36,5,38,61,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta26));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Tables.mo",36,5,38,61,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta26));
        }
      }
      tmp27 = 1;
    }
  }
  threadData->lastEquationSolved = 329;
}

/*
equation index: 330
type: ALGORITHM

  assert(p_ambient >= 0.0, "Variable violating min constraint: 0.0 <= p_ambient, has value: " + String(p_ambient, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_330(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,330};
  modelica_boolean tmp28;
  static const MMC_DEFSTRINGLIT(tmp29,64,"Variable violating min constraint: 0.0 <= p_ambient, has value: ");
  modelica_string tmp30;
  modelica_metatype tmpMeta31;
  static int tmp32 = 0;
  if(!tmp32)
  {
    tmp28 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[141]] /* p_ambient PARAM */),0.0);
    if(!tmp28)
    {
      tmp30 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[141]] /* p_ambient PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta31 = stringAppend(MMC_REFSTRINGLIT(tmp29),tmp30);
      {
        const char* assert_cond = "(p_ambient >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Examples/HydraulicsStep.mo",5,3,5,92,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta31));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Examples/HydraulicsStep.mo",5,3,5,92,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta31));
        }
      }
      tmp32 = 1;
    }
  }
  threadData->lastEquationSolved = 330;
}

/*
equation index: 331
type: ALGORITHM

  assert(chamberR.p_ambient >= 0.0, "Variable violating min constraint: 0.0 <= chamberR.p_ambient, has value: " + String(chamberR.p_ambient, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_331(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,331};
  modelica_boolean tmp33;
  static const MMC_DEFSTRINGLIT(tmp34,73,"Variable violating min constraint: 0.0 <= chamberR.p_ambient, has value: ");
  modelica_string tmp35;
  modelica_metatype tmpMeta36;
  static int tmp37 = 0;
  if(!tmp37)
  {
    tmp33 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[81]] /* chamberR.p_ambient PARAM */),0.0);
    if(!tmp33)
    {
      tmp35 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[81]] /* chamberR.p_ambient PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta36 = stringAppend(MMC_REFSTRINGLIT(tmp34),tmp35);
      {
        const char* assert_cond = "(chamberR.p_ambient >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Chamber.mo",3,3,4,99,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta36));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Chamber.mo",3,3,4,99,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta36));
        }
      }
      tmp37 = 1;
    }
  }
  threadData->lastEquationSolved = 331;
}

/*
equation index: 332
type: ALGORITHM

  assert(chamberL.pV.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and chamberL.pV.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, "Variable violating min/max constraint: Modelica.Blocks.Types.Extrapolation.HoldLastPoint <= chamberL.pV.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, has value: " + String(chamberL.pV.extrapolation, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_332(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,332};
  modelica_boolean tmp38;
  modelica_boolean tmp39;
  static const MMC_DEFSTRINGLIT(tmp40,185,"Variable violating min/max constraint: Modelica.Blocks.Types.Extrapolation.HoldLastPoint <= chamberL.pV.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, has value: ");
  modelica_string tmp41;
  modelica_metatype tmpMeta42;
  static int tmp43 = 0;
  if(!tmp43)
  {
    tmp38 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[2]] /* chamberL.pV.extrapolation PARAM */),1);
    tmp39 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[2]] /* chamberL.pV.extrapolation PARAM */),4);
    if(!(tmp38 && tmp39))
    {
      tmp41 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[2]] /* chamberL.pV.extrapolation PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta42 = stringAppend(MMC_REFSTRINGLIT(tmp40),tmp41);
      {
        const char* assert_cond = "(chamberL.pV.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and chamberL.pV.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Tables.mo",39,5,41,61,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta42));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Tables.mo",39,5,41,61,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta42));
        }
      }
      tmp43 = 1;
    }
  }
  threadData->lastEquationSolved = 332;
}

/*
equation index: 333
type: ALGORITHM

  assert(chamberL.pV.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and chamberL.pV.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, "Variable violating min/max constraint: Modelica.Blocks.Types.Smoothness.LinearSegments <= chamberL.pV.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, has value: " + String(chamberL.pV.smoothness, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_333(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,333};
  modelica_boolean tmp44;
  modelica_boolean tmp45;
  static const MMC_DEFSTRINGLIT(tmp46,190,"Variable violating min/max constraint: Modelica.Blocks.Types.Smoothness.LinearSegments <= chamberL.pV.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, has value: ");
  modelica_string tmp47;
  modelica_metatype tmpMeta48;
  static int tmp49 = 0;
  if(!tmp49)
  {
    tmp44 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[5]] /* chamberL.pV.smoothness PARAM */),1);
    tmp45 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[5]] /* chamberL.pV.smoothness PARAM */),6);
    if(!(tmp44 && tmp45))
    {
      tmp47 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[5]] /* chamberL.pV.smoothness PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta48 = stringAppend(MMC_REFSTRINGLIT(tmp46),tmp47);
      {
        const char* assert_cond = "(chamberL.pV.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and chamberL.pV.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Tables.mo",36,5,38,61,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta48));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Tables.mo",36,5,38,61,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta48));
        }
      }
      tmp49 = 1;
    }
  }
  threadData->lastEquationSolved = 333;
}

/*
equation index: 334
type: ALGORITHM

  assert(chamberL.p_ambient >= 0.0, "Variable violating min constraint: 0.0 <= chamberL.p_ambient, has value: " + String(chamberL.p_ambient, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_334(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,334};
  modelica_boolean tmp50;
  static const MMC_DEFSTRINGLIT(tmp51,73,"Variable violating min constraint: 0.0 <= chamberL.p_ambient, has value: ");
  modelica_string tmp52;
  modelica_metatype tmpMeta53;
  static int tmp54 = 0;
  if(!tmp54)
  {
    tmp50 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[33]] /* chamberL.p_ambient PARAM */),0.0);
    if(!tmp50)
    {
      tmp52 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[33]] /* chamberL.p_ambient PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta53 = stringAppend(MMC_REFSTRINGLIT(tmp51),tmp52);
      {
        const char* assert_cond = "(chamberL.p_ambient >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Chamber.mo",3,3,4,99,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta53));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Chamber.mo",3,3,4,99,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta53));
        }
      }
      tmp54 = 1;
    }
  }
  threadData->lastEquationSolved = 334;
}

/*
equation index: 335
type: ALGORITHM

  assert(pipeR.rho >= 0.0, "Variable violating min constraint: 0.0 <= pipeR.rho, has value: " + String(pipeR.rho, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_335(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,335};
  modelica_boolean tmp55;
  static const MMC_DEFSTRINGLIT(tmp56,64,"Variable violating min constraint: 0.0 <= pipeR.rho, has value: ");
  modelica_string tmp57;
  modelica_metatype tmpMeta58;
  static int tmp59 = 0;
  if(!tmp59)
  {
    tmp55 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[162]] /* pipeR.rho PARAM */),0.0);
    if(!tmp55)
    {
      tmp57 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[162]] /* pipeR.rho PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta58 = stringAppend(MMC_REFSTRINGLIT(tmp56),tmp57);
      {
        const char* assert_cond = "(pipeR.rho >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",9,3,9,81,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta58));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",9,3,9,81,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta58));
        }
      }
      tmp59 = 1;
    }
  }
  threadData->lastEquationSolved = 335;
}

/*
equation index: 336
type: ALGORITHM

  assert(pipeR.d >= 0.0, "Variable violating min constraint: 0.0 <= pipeR.d, has value: " + String(pipeR.d, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_336(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,336};
  modelica_boolean tmp60;
  static const MMC_DEFSTRINGLIT(tmp61,62,"Variable violating min constraint: 0.0 <= pipeR.d, has value: ");
  modelica_string tmp62;
  modelica_metatype tmpMeta63;
  static int tmp64 = 0;
  if(!tmp64)
  {
    tmp60 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[159]] /* pipeR.d PARAM */),0.0);
    if(!tmp60)
    {
      tmp62 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[159]] /* pipeR.d PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta63 = stringAppend(MMC_REFSTRINGLIT(tmp61),tmp62);
      {
        const char* assert_cond = "(pipeR.d >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",7,3,7,107,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta63));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",7,3,7,107,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta63));
        }
      }
      tmp64 = 1;
    }
  }
  threadData->lastEquationSolved = 336;
}

/*
equation index: 337
type: ALGORITHM

  assert(pipeR.zeta >= 0.0, "Variable violating min constraint: 0.0 <= pipeR.zeta, has value: " + String(pipeR.zeta, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_337(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,337};
  modelica_boolean tmp65;
  static const MMC_DEFSTRINGLIT(tmp66,65,"Variable violating min constraint: 0.0 <= pipeR.zeta, has value: ");
  modelica_string tmp67;
  modelica_metatype tmpMeta68;
  static int tmp69 = 0;
  if(!tmp69)
  {
    tmp65 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[163]] /* pipeR.zeta PARAM */),0.0);
    if(!tmp65)
    {
      tmp67 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[163]] /* pipeR.zeta PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta68 = stringAppend(MMC_REFSTRINGLIT(tmp66),tmp67);
      {
        const char* assert_cond = "(pipeR.zeta >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",8,3,8,125,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta68));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",8,3,8,125,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta68));
        }
      }
      tmp69 = 1;
    }
  }
  threadData->lastEquationSolved = 337;
}

/*
equation index: 338
type: ALGORITHM

  assert(pipeR.mu >= 0.0, "Variable violating min constraint: 0.0 <= pipeR.mu, has value: " + String(pipeR.mu, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_338(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,338};
  modelica_boolean tmp70;
  static const MMC_DEFSTRINGLIT(tmp71,63,"Variable violating min constraint: 0.0 <= pipeR.mu, has value: ");
  modelica_string tmp72;
  modelica_metatype tmpMeta73;
  static int tmp74 = 0;
  if(!tmp74)
  {
    tmp70 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[161]] /* pipeR.mu PARAM */),0.0);
    if(!tmp70)
    {
      tmp72 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[161]] /* pipeR.mu PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta73 = stringAppend(MMC_REFSTRINGLIT(tmp71),tmp72);
      {
        const char* assert_cond = "(pipeR.mu >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",10,3,10,102,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta73));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",10,3,10,102,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta73));
        }
      }
      tmp74 = 1;
    }
  }
  threadData->lastEquationSolved = 338;
}

/*
equation index: 339
type: ALGORITHM

  assert(pipeL.rho >= 0.0, "Variable violating min constraint: 0.0 <= pipeL.rho, has value: " + String(pipeL.rho, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_339(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,339};
  modelica_boolean tmp75;
  static const MMC_DEFSTRINGLIT(tmp76,64,"Variable violating min constraint: 0.0 <= pipeL.rho, has value: ");
  modelica_string tmp77;
  modelica_metatype tmpMeta78;
  static int tmp79 = 0;
  if(!tmp79)
  {
    tmp75 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[151]] /* pipeL.rho PARAM */),0.0);
    if(!tmp75)
    {
      tmp77 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[151]] /* pipeL.rho PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta78 = stringAppend(MMC_REFSTRINGLIT(tmp76),tmp77);
      {
        const char* assert_cond = "(pipeL.rho >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",9,3,9,81,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta78));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",9,3,9,81,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta78));
        }
      }
      tmp79 = 1;
    }
  }
  threadData->lastEquationSolved = 339;
}

/*
equation index: 340
type: ALGORITHM

  assert(pipeL.d >= 0.0, "Variable violating min constraint: 0.0 <= pipeL.d, has value: " + String(pipeL.d, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_340(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,340};
  modelica_boolean tmp80;
  static const MMC_DEFSTRINGLIT(tmp81,62,"Variable violating min constraint: 0.0 <= pipeL.d, has value: ");
  modelica_string tmp82;
  modelica_metatype tmpMeta83;
  static int tmp84 = 0;
  if(!tmp84)
  {
    tmp80 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[148]] /* pipeL.d PARAM */),0.0);
    if(!tmp80)
    {
      tmp82 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[148]] /* pipeL.d PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta83 = stringAppend(MMC_REFSTRINGLIT(tmp81),tmp82);
      {
        const char* assert_cond = "(pipeL.d >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",7,3,7,107,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta83));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",7,3,7,107,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta83));
        }
      }
      tmp84 = 1;
    }
  }
  threadData->lastEquationSolved = 340;
}

/*
equation index: 341
type: ALGORITHM

  assert(pipeL.zeta >= 0.0, "Variable violating min constraint: 0.0 <= pipeL.zeta, has value: " + String(pipeL.zeta, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_341(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,341};
  modelica_boolean tmp85;
  static const MMC_DEFSTRINGLIT(tmp86,65,"Variable violating min constraint: 0.0 <= pipeL.zeta, has value: ");
  modelica_string tmp87;
  modelica_metatype tmpMeta88;
  static int tmp89 = 0;
  if(!tmp89)
  {
    tmp85 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[152]] /* pipeL.zeta PARAM */),0.0);
    if(!tmp85)
    {
      tmp87 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[152]] /* pipeL.zeta PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta88 = stringAppend(MMC_REFSTRINGLIT(tmp86),tmp87);
      {
        const char* assert_cond = "(pipeL.zeta >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",8,3,8,125,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta88));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",8,3,8,125,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta88));
        }
      }
      tmp89 = 1;
    }
  }
  threadData->lastEquationSolved = 341;
}

/*
equation index: 342
type: ALGORITHM

  assert(pipeL.mu >= 0.0, "Variable violating min constraint: 0.0 <= pipeL.mu, has value: " + String(pipeL.mu, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_342(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,342};
  modelica_boolean tmp90;
  static const MMC_DEFSTRINGLIT(tmp91,63,"Variable violating min constraint: 0.0 <= pipeL.mu, has value: ");
  modelica_string tmp92;
  modelica_metatype tmpMeta93;
  static int tmp94 = 0;
  if(!tmp94)
  {
    tmp90 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[150]] /* pipeL.mu PARAM */),0.0);
    if(!tmp90)
    {
      tmp92 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[150]] /* pipeL.mu PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta93 = stringAppend(MMC_REFSTRINGLIT(tmp91),tmp92);
      {
        const char* assert_cond = "(pipeL.mu >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",10,3,10,102,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta93));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/Pipe.mo",10,3,10,102,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta93));
        }
      }
      tmp94 = 1;
    }
  }
  threadData->lastEquationSolved = 342;
}

/*
equation index: 343
type: ALGORITHM

  assert(pump.eta_m >= 0.1 and pump.eta_m <= 1.0, "Variable violating min/max constraint: 0.1 <= pump.eta_m <= 1.0, has value: " + String(pump.eta_m, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_343(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,343};
  modelica_boolean tmp95;
  modelica_boolean tmp96;
  static const MMC_DEFSTRINGLIT(tmp97,76,"Variable violating min/max constraint: 0.1 <= pump.eta_m <= 1.0, has value: ");
  modelica_string tmp98;
  modelica_metatype tmpMeta99;
  static int tmp100 = 0;
  if(!tmp100)
  {
    tmp95 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[166]] /* pump.eta_m PARAM */),0.1);
    tmp96 = LessEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[166]] /* pump.eta_m PARAM */),1.0);
    if(!(tmp95 && tmp96))
    {
      tmp98 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[166]] /* pump.eta_m PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta99 = stringAppend(MMC_REFSTRINGLIT(tmp97),tmp98);
      {
        const char* assert_cond = "(pump.eta_m >= 0.1 and pump.eta_m <= 1.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/GearPump.mo",10,3,10,106,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta99));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Hydraulics/GearPump.mo",10,3,10,106,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta99));
        }
      }
      tmp100 = 1;
    }
  }
  threadData->lastEquationSolved = 343;
}

/*
equation index: 344
type: ALGORITHM

  assert(command.timeScale >= 2.220446049250313e-16, "Variable violating min constraint: 2.220446049250313e-16 <= command.timeScale, has value: " + String(command.timeScale, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_344(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,344};
  modelica_boolean tmp101;
  static const MMC_DEFSTRINGLIT(tmp102,90,"Variable violating min constraint: 2.220446049250313e-16 <= command.timeScale, has value: ");
  modelica_string tmp103;
  modelica_metatype tmpMeta104;
  static int tmp105 = 0;
  if(!tmp105)
  {
    tmp101 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[124]] /* command.timeScale PARAM */),2.220446049250313e-16);
    if(!tmp101)
    {
      tmp103 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[124]] /* command.timeScale PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta104 = stringAppend(MMC_REFSTRINGLIT(tmp102),tmp103);
      {
        const char* assert_cond = "(command.timeScale >= 2.220446049250313e-16)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Sources.mo",1627,5,1629,76,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta104));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Sources.mo",1627,5,1629,76,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta104));
        }
      }
      tmp105 = 1;
    }
  }
  threadData->lastEquationSolved = 344;
}

/*
equation index: 345
type: ALGORITHM

  assert(command.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and command.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, "Variable violating min/max constraint: Modelica.Blocks.Types.Extrapolation.HoldLastPoint <= command.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, has value: " + String(command.extrapolation, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_345(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,345};
  modelica_boolean tmp106;
  modelica_boolean tmp107;
  static const MMC_DEFSTRINGLIT(tmp108,181,"Variable violating min/max constraint: Modelica.Blocks.Types.Extrapolation.HoldLastPoint <= command.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation, has value: ");
  modelica_string tmp109;
  modelica_metatype tmpMeta110;
  static int tmp111 = 0;
  if(!tmp111)
  {
    tmp106 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[13]] /* command.extrapolation PARAM */),1);
    tmp107 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[13]] /* command.extrapolation PARAM */),4);
    if(!(tmp106 && tmp107))
    {
      tmp109 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[13]] /* command.extrapolation PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta110 = stringAppend(MMC_REFSTRINGLIT(tmp108),tmp109);
      {
        const char* assert_cond = "(command.extrapolation >= Modelica.Blocks.Types.Extrapolation.HoldLastPoint and command.extrapolation <= Modelica.Blocks.Types.Extrapolation.NoExtrapolation)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Sources.mo",1624,5,1626,61,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta110));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Sources.mo",1624,5,1626,61,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta110));
        }
      }
      tmp111 = 1;
    }
  }
  threadData->lastEquationSolved = 345;
}

/*
equation index: 346
type: ALGORITHM

  assert(command.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and command.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, "Variable violating min/max constraint: Modelica.Blocks.Types.Smoothness.LinearSegments <= command.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, has value: " + String(command.smoothness, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_346(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,346};
  modelica_boolean tmp112;
  modelica_boolean tmp113;
  static const MMC_DEFSTRINGLIT(tmp114,186,"Variable violating min/max constraint: Modelica.Blocks.Types.Smoothness.LinearSegments <= command.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative, has value: ");
  modelica_string tmp115;
  modelica_metatype tmpMeta116;
  static int tmp117 = 0;
  if(!tmp117)
  {
    tmp112 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[16]] /* command.smoothness PARAM */),1);
    tmp113 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[16]] /* command.smoothness PARAM */),6);
    if(!(tmp112 && tmp113))
    {
      tmp115 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[16]] /* command.smoothness PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta116 = stringAppend(MMC_REFSTRINGLIT(tmp114),tmp115);
      {
        const char* assert_cond = "(command.smoothness >= Modelica.Blocks.Types.Smoothness.LinearSegments and command.smoothness <= Modelica.Blocks.Types.Smoothness.ModifiedContinuousDerivative)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Sources.mo",1621,5,1623,61,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta116));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Sources.mo",1621,5,1623,61,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta116));
        }
      }
      tmp117 = 1;
    }
  }
  threadData->lastEquationSolved = 346;
}

/*
equation index: 347
type: ALGORITHM

  assert(command.nout >= 1, "Variable violating min constraint: 1 <= command.nout, has value: " + String(command.nout, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_347(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,347};
  modelica_boolean tmp118;
  static const MMC_DEFSTRINGLIT(tmp119,65,"Variable violating min constraint: 1 <= command.nout, has value: ");
  modelica_string tmp120;
  modelica_metatype tmpMeta121;
  static int tmp122 = 0;
  if(!tmp122)
  {
    tmp118 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[15]] /* command.nout PARAM */),((modelica_integer) 1));
    if(!tmp118)
    {
      tmp120 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[15]] /* command.nout PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta121 = stringAppend(MMC_REFSTRINGLIT(tmp119),tmp120);
      {
        const char* assert_cond = "(command.nout >= 1)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Interfaces.mo",313,5,313,58,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta121));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Blocks/Interfaces.mo",313,5,313,58,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta121));
        }
      }
      tmp122 = 1;
    }
  }
  threadData->lastEquationSolved = 347;
}

/*
equation index: 348
type: ALGORITHM

  assert(motor.friction.d >= 0.0, "Variable violating min constraint: 0.0 <= motor.friction.d, has value: " + String(motor.friction.d, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_348(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,348};
  modelica_boolean tmp123;
  static const MMC_DEFSTRINGLIT(tmp124,71,"Variable violating min constraint: 0.0 <= motor.friction.d, has value: ");
  modelica_string tmp125;
  modelica_metatype tmpMeta126;
  static int tmp127 = 0;
  if(!tmp127)
  {
    tmp123 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[131]] /* motor.friction.d PARAM */),0.0);
    if(!tmp123)
    {
      tmp125 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[131]] /* motor.friction.d PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta126 = stringAppend(MMC_REFSTRINGLIT(tmp124),tmp125);
      {
        const char* assert_cond = "(motor.friction.d >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Components/Damper.mo",5,3,6,23,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta126));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Components/Damper.mo",5,3,6,23,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta126));
        }
      }
      tmp127 = 1;
    }
  }
  threadData->lastEquationSolved = 348;
}

/*
equation index: 349
type: ALGORITHM

  assert(motor.friction.stateSelect >= StateSelect.never and motor.friction.stateSelect <= StateSelect.always, "Variable violating min/max constraint: StateSelect.never <= motor.friction.stateSelect <= StateSelect.always, has value: " + String(motor.friction.stateSelect, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_349(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,349};
  modelica_boolean tmp128;
  modelica_boolean tmp129;
  static const MMC_DEFSTRINGLIT(tmp130,121,"Variable violating min/max constraint: StateSelect.never <= motor.friction.stateSelect <= StateSelect.always, has value: ");
  modelica_string tmp131;
  modelica_metatype tmpMeta132;
  static int tmp133 = 0;
  if(!tmp133)
  {
    tmp128 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[18]] /* motor.friction.stateSelect PARAM */),1);
    tmp129 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[18]] /* motor.friction.stateSelect PARAM */),5);
    if(!(tmp128 && tmp129))
    {
      tmp131 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[18]] /* motor.friction.stateSelect PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta132 = stringAppend(MMC_REFSTRINGLIT(tmp130),tmp131);
      {
        const char* assert_cond = "(motor.friction.stateSelect >= StateSelect.never and motor.friction.stateSelect <= StateSelect.always)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Interfaces/PartialCompliantWithRelativeStates.mo",24,3,26,57,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta132));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Interfaces/PartialCompliantWithRelativeStates.mo",24,3,26,57,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta132));
        }
      }
      tmp133 = 1;
    }
  }
  threadData->lastEquationSolved = 349;
}

/*
equation index: 350
type: ALGORITHM

  assert(motor.friction.phi_nominal >= 0.0, "Variable violating min constraint: 0.0 <= motor.friction.phi_nominal, has value: " + String(motor.friction.phi_nominal, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_350(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,350};
  modelica_boolean tmp134;
  static const MMC_DEFSTRINGLIT(tmp135,81,"Variable violating min constraint: 0.0 <= motor.friction.phi_nominal, has value: ");
  modelica_string tmp136;
  modelica_metatype tmpMeta137;
  static int tmp138 = 0;
  if(!tmp138)
  {
    tmp134 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[132]] /* motor.friction.phi_nominal PARAM */),0.0);
    if(!tmp134)
    {
      tmp136 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[132]] /* motor.friction.phi_nominal PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta137 = stringAppend(MMC_REFSTRINGLIT(tmp135),tmp136);
      {
        const char* assert_cond = "(motor.friction.phi_nominal >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Interfaces/PartialCompliantWithRelativeStates.mo",20,3,23,40,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta137));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Interfaces/PartialCompliantWithRelativeStates.mo",20,3,23,40,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta137));
        }
      }
      tmp138 = 1;
    }
  }
  threadData->lastEquationSolved = 350;
}

/*
equation index: 351
type: ALGORITHM

  assert(motor.rotor.stateSelect >= StateSelect.never and motor.rotor.stateSelect <= StateSelect.always, "Variable violating min/max constraint: StateSelect.never <= motor.rotor.stateSelect <= StateSelect.always, has value: " + String(motor.rotor.stateSelect, "d"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_351(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,351};
  modelica_boolean tmp139;
  modelica_boolean tmp140;
  static const MMC_DEFSTRINGLIT(tmp141,118,"Variable violating min/max constraint: StateSelect.never <= motor.rotor.stateSelect <= StateSelect.always, has value: ");
  modelica_string tmp142;
  modelica_metatype tmpMeta143;
  static int tmp144 = 0;
  if(!tmp144)
  {
    tmp139 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[19]] /* motor.rotor.stateSelect PARAM */),1);
    tmp140 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[19]] /* motor.rotor.stateSelect PARAM */),5);
    if(!(tmp139 && tmp140))
    {
      tmp142 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[19]] /* motor.rotor.stateSelect PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta143 = stringAppend(MMC_REFSTRINGLIT(tmp141),tmp142);
      {
        const char* assert_cond = "(motor.rotor.stateSelect >= StateSelect.never and motor.rotor.stateSelect <= StateSelect.always)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Components/Inertia.mo",5,3,7,57,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta143));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Components/Inertia.mo",5,3,7,57,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta143));
        }
      }
      tmp144 = 1;
    }
  }
  threadData->lastEquationSolved = 351;
}

/*
equation index: 352
type: ALGORITHM

  assert(motor.rotor.J >= 0.0, "Variable violating min constraint: 0.0 <= motor.rotor.J, has value: " + String(motor.rotor.J, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_352(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,352};
  modelica_boolean tmp145;
  static const MMC_DEFSTRINGLIT(tmp146,68,"Variable violating min constraint: 0.0 <= motor.rotor.J, has value: ");
  modelica_string tmp147;
  modelica_metatype tmpMeta148;
  static int tmp149 = 0;
  if(!tmp149)
  {
    tmp145 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[140]] /* motor.rotor.J PARAM */),0.0);
    if(!tmp145)
    {
      tmp147 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[140]] /* motor.rotor.J PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta148 = stringAppend(MMC_REFSTRINGLIT(tmp146),tmp147);
      {
        const char* assert_cond = "(motor.rotor.J >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Components/Inertia.mo",4,3,4,61,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta148));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Mechanics/Rotational/Components/Inertia.mo",4,3,4,61,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta148));
        }
      }
      tmp149 = 1;
    }
  }
  threadData->lastEquationSolved = 352;
}

/*
equation index: 353
type: ALGORITHM

  assert(motor.resistor.T_ref >= 0.0, "Variable violating min constraint: 0.0 <= motor.resistor.T_ref, has value: " + String(motor.resistor.T_ref, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_353(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,353};
  modelica_boolean tmp150;
  static const MMC_DEFSTRINGLIT(tmp151,75,"Variable violating min constraint: 0.0 <= motor.resistor.T_ref, has value: ");
  modelica_string tmp152;
  modelica_metatype tmpMeta153;
  static int tmp154 = 0;
  if(!tmp154)
  {
    tmp150 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[138]] /* motor.resistor.T_ref PARAM */),0.0);
    if(!tmp150)
    {
      tmp152 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[138]] /* motor.resistor.T_ref PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta153 = stringAppend(MMC_REFSTRINGLIT(tmp151),tmp152);
      {
        const char* assert_cond = "(motor.resistor.T_ref >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta153));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta153));
        }
      }
      tmp154 = 1;
    }
  }
  threadData->lastEquationSolved = 353;
}

/*
equation index: 354
type: ALGORITHM

  assert(motor.resistor.T >= 0.0, "Variable violating min constraint: 0.0 <= motor.resistor.T, has value: " + String(motor.resistor.T, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_354(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,354};
  modelica_boolean tmp155;
  static const MMC_DEFSTRINGLIT(tmp156,71,"Variable violating min constraint: 0.0 <= motor.resistor.T, has value: ");
  modelica_string tmp157;
  modelica_metatype tmpMeta158;
  static int tmp159 = 0;
  if(!tmp159)
  {
    tmp155 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[137]] /* motor.resistor.T PARAM */),0.0);
    if(!tmp155)
    {
      tmp157 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[137]] /* motor.resistor.T PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta158 = stringAppend(MMC_REFSTRINGLIT(tmp156),tmp157);
      {
        const char* assert_cond = "(motor.resistor.T >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta158));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta158));
        }
      }
      tmp159 = 1;
    }
  }
  threadData->lastEquationSolved = 354;
}

/*
equation index: 355
type: ALGORITHM

  assert(battery.rInt.T_ref >= 0.0, "Variable violating min constraint: 0.0 <= battery.rInt.T_ref, has value: " + String(battery.rInt.T_ref, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_355(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,355};
  modelica_boolean tmp160;
  static const MMC_DEFSTRINGLIT(tmp161,73,"Variable violating min constraint: 0.0 <= battery.rInt.T_ref, has value: ");
  modelica_string tmp162;
  modelica_metatype tmpMeta163;
  static int tmp164 = 0;
  if(!tmp164)
  {
    tmp160 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* battery.rInt.T_ref PARAM */),0.0);
    if(!tmp160)
    {
      tmp162 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* battery.rInt.T_ref PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta163 = stringAppend(MMC_REFSTRINGLIT(tmp161),tmp162);
      {
        const char* assert_cond = "(battery.rInt.T_ref >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta163));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",5,3,5,64,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta163));
        }
      }
      tmp164 = 1;
    }
  }
  threadData->lastEquationSolved = 355;
}

/*
equation index: 356
type: ALGORITHM

  assert(battery.rInt.T >= 0.0, "Variable violating min constraint: 0.0 <= battery.rInt.T, has value: " + String(battery.rInt.T, "g"));
*/
OMC_DISABLE_OPT
static void FishRobot_Examples_HydraulicsStep_eqFunction_356(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,356};
  modelica_boolean tmp165;
  static const MMC_DEFSTRINGLIT(tmp166,69,"Variable violating min constraint: 0.0 <= battery.rInt.T, has value: ");
  modelica_string tmp167;
  modelica_metatype tmpMeta168;
  static int tmp169 = 0;
  if(!tmp169)
  {
    tmp165 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* battery.rInt.T PARAM */),0.0);
    if(!tmp165)
    {
      tmp167 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* battery.rInt.T PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta168 = stringAppend(MMC_REFSTRINGLIT(tmp166),tmp167);
      {
        const char* assert_cond = "(battery.rInt.T >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta168));
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Interfaces/ConditionalHeatPort.mo",7,3,8,97,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta168));
        }
      }
      tmp169 = 1;
    }
  }
  threadData->lastEquationSolved = 356;
}
OMC_DISABLE_OPT
void FishRobot_Examples_HydraulicsStep_updateBoundParameters_0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[122])(DATA*, threadData_t*) = {
    FishRobot_Examples_HydraulicsStep_eqFunction_199,
    FishRobot_Examples_HydraulicsStep_eqFunction_200,
    FishRobot_Examples_HydraulicsStep_eqFunction_201,
    FishRobot_Examples_HydraulicsStep_eqFunction_202,
    FishRobot_Examples_HydraulicsStep_eqFunction_203,
    FishRobot_Examples_HydraulicsStep_eqFunction_204,
    FishRobot_Examples_HydraulicsStep_eqFunction_205,
    FishRobot_Examples_HydraulicsStep_eqFunction_206,
    FishRobot_Examples_HydraulicsStep_eqFunction_207,
    FishRobot_Examples_HydraulicsStep_eqFunction_208,
    FishRobot_Examples_HydraulicsStep_eqFunction_209,
    FishRobot_Examples_HydraulicsStep_eqFunction_210,
    FishRobot_Examples_HydraulicsStep_eqFunction_211,
    FishRobot_Examples_HydraulicsStep_eqFunction_212,
    FishRobot_Examples_HydraulicsStep_eqFunction_213,
    FishRobot_Examples_HydraulicsStep_eqFunction_214,
    FishRobot_Examples_HydraulicsStep_eqFunction_215,
    FishRobot_Examples_HydraulicsStep_eqFunction_216,
    FishRobot_Examples_HydraulicsStep_eqFunction_217,
    FishRobot_Examples_HydraulicsStep_eqFunction_218,
    FishRobot_Examples_HydraulicsStep_eqFunction_219,
    FishRobot_Examples_HydraulicsStep_eqFunction_220,
    FishRobot_Examples_HydraulicsStep_eqFunction_221,
    FishRobot_Examples_HydraulicsStep_eqFunction_222,
    FishRobot_Examples_HydraulicsStep_eqFunction_223,
    FishRobot_Examples_HydraulicsStep_eqFunction_224,
    FishRobot_Examples_HydraulicsStep_eqFunction_225,
    FishRobot_Examples_HydraulicsStep_eqFunction_226,
    FishRobot_Examples_HydraulicsStep_eqFunction_227,
    FishRobot_Examples_HydraulicsStep_eqFunction_228,
    FishRobot_Examples_HydraulicsStep_eqFunction_229,
    FishRobot_Examples_HydraulicsStep_eqFunction_230,
    FishRobot_Examples_HydraulicsStep_eqFunction_231,
    FishRobot_Examples_HydraulicsStep_eqFunction_232,
    FishRobot_Examples_HydraulicsStep_eqFunction_233,
    FishRobot_Examples_HydraulicsStep_eqFunction_234,
    FishRobot_Examples_HydraulicsStep_eqFunction_235,
    FishRobot_Examples_HydraulicsStep_eqFunction_236,
    FishRobot_Examples_HydraulicsStep_eqFunction_237,
    FishRobot_Examples_HydraulicsStep_eqFunction_238,
    FishRobot_Examples_HydraulicsStep_eqFunction_239,
    FishRobot_Examples_HydraulicsStep_eqFunction_240,
    FishRobot_Examples_HydraulicsStep_eqFunction_241,
    FishRobot_Examples_HydraulicsStep_eqFunction_242,
    FishRobot_Examples_HydraulicsStep_eqFunction_243,
    FishRobot_Examples_HydraulicsStep_eqFunction_244,
    FishRobot_Examples_HydraulicsStep_eqFunction_245,
    FishRobot_Examples_HydraulicsStep_eqFunction_246,
    FishRobot_Examples_HydraulicsStep_eqFunction_247,
    FishRobot_Examples_HydraulicsStep_eqFunction_248,
    FishRobot_Examples_HydraulicsStep_eqFunction_249,
    FishRobot_Examples_HydraulicsStep_eqFunction_250,
    FishRobot_Examples_HydraulicsStep_eqFunction_251,
    FishRobot_Examples_HydraulicsStep_eqFunction_252,
    FishRobot_Examples_HydraulicsStep_eqFunction_254,
    FishRobot_Examples_HydraulicsStep_eqFunction_255,
    FishRobot_Examples_HydraulicsStep_eqFunction_261,
    FishRobot_Examples_HydraulicsStep_eqFunction_262,
    FishRobot_Examples_HydraulicsStep_eqFunction_266,
    FishRobot_Examples_HydraulicsStep_eqFunction_267,
    FishRobot_Examples_HydraulicsStep_eqFunction_269,
    FishRobot_Examples_HydraulicsStep_eqFunction_270,
    FishRobot_Examples_HydraulicsStep_eqFunction_276,
    FishRobot_Examples_HydraulicsStep_eqFunction_277,
    FishRobot_Examples_HydraulicsStep_eqFunction_281,
    FishRobot_Examples_HydraulicsStep_eqFunction_282,
    FishRobot_Examples_HydraulicsStep_eqFunction_283,
    FishRobot_Examples_HydraulicsStep_eqFunction_284,
    FishRobot_Examples_HydraulicsStep_eqFunction_285,
    FishRobot_Examples_HydraulicsStep_eqFunction_286,
    FishRobot_Examples_HydraulicsStep_eqFunction_288,
    FishRobot_Examples_HydraulicsStep_eqFunction_289,
    FishRobot_Examples_HydraulicsStep_eqFunction_290,
    FishRobot_Examples_HydraulicsStep_eqFunction_291,
    FishRobot_Examples_HydraulicsStep_eqFunction_293,
    FishRobot_Examples_HydraulicsStep_eqFunction_295,
    FishRobot_Examples_HydraulicsStep_eqFunction_296,
    FishRobot_Examples_HydraulicsStep_eqFunction_297,
    FishRobot_Examples_HydraulicsStep_eqFunction_298,
    FishRobot_Examples_HydraulicsStep_eqFunction_299,
    FishRobot_Examples_HydraulicsStep_eqFunction_307,
    FishRobot_Examples_HydraulicsStep_eqFunction_310,
    FishRobot_Examples_HydraulicsStep_eqFunction_312,
    FishRobot_Examples_HydraulicsStep_eqFunction_314,
    FishRobot_Examples_HydraulicsStep_eqFunction_315,
    FishRobot_Examples_HydraulicsStep_eqFunction_317,
    FishRobot_Examples_HydraulicsStep_eqFunction_319,
    FishRobot_Examples_HydraulicsStep_eqFunction_322,
    FishRobot_Examples_HydraulicsStep_eqFunction_323,
    FishRobot_Examples_HydraulicsStep_eqFunction_92,
    FishRobot_Examples_HydraulicsStep_eqFunction_2,
    FishRobot_Examples_HydraulicsStep_eqFunction_1,
    FishRobot_Examples_HydraulicsStep_eqFunction_327,
    FishRobot_Examples_HydraulicsStep_eqFunction_328,
    FishRobot_Examples_HydraulicsStep_eqFunction_329,
    FishRobot_Examples_HydraulicsStep_eqFunction_330,
    FishRobot_Examples_HydraulicsStep_eqFunction_331,
    FishRobot_Examples_HydraulicsStep_eqFunction_332,
    FishRobot_Examples_HydraulicsStep_eqFunction_333,
    FishRobot_Examples_HydraulicsStep_eqFunction_334,
    FishRobot_Examples_HydraulicsStep_eqFunction_335,
    FishRobot_Examples_HydraulicsStep_eqFunction_336,
    FishRobot_Examples_HydraulicsStep_eqFunction_337,
    FishRobot_Examples_HydraulicsStep_eqFunction_338,
    FishRobot_Examples_HydraulicsStep_eqFunction_339,
    FishRobot_Examples_HydraulicsStep_eqFunction_340,
    FishRobot_Examples_HydraulicsStep_eqFunction_341,
    FishRobot_Examples_HydraulicsStep_eqFunction_342,
    FishRobot_Examples_HydraulicsStep_eqFunction_343,
    FishRobot_Examples_HydraulicsStep_eqFunction_344,
    FishRobot_Examples_HydraulicsStep_eqFunction_345,
    FishRobot_Examples_HydraulicsStep_eqFunction_346,
    FishRobot_Examples_HydraulicsStep_eqFunction_347,
    FishRobot_Examples_HydraulicsStep_eqFunction_348,
    FishRobot_Examples_HydraulicsStep_eqFunction_349,
    FishRobot_Examples_HydraulicsStep_eqFunction_350,
    FishRobot_Examples_HydraulicsStep_eqFunction_351,
    FishRobot_Examples_HydraulicsStep_eqFunction_352,
    FishRobot_Examples_HydraulicsStep_eqFunction_353,
    FishRobot_Examples_HydraulicsStep_eqFunction_354,
    FishRobot_Examples_HydraulicsStep_eqFunction_355,
    FishRobot_Examples_HydraulicsStep_eqFunction_356
  };
  
  for (int id = 0; id < 122; id++) {
    eqFunctions[id](data, threadData);
  }
}
OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_updateBoundParameters(DATA *data, threadData_t *threadData)
{
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[1]] /* chamberL.pV.columns[1] PARAM */) = ((modelica_integer) 2);
  data->modelData->integerParameterData[1].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[4]] /* chamberL.pV.nout PARAM */) = ((modelica_integer) 1);
  data->modelData->integerParameterData[4].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[7]] /* chamberR.pV.columns[1] PARAM */) = ((modelica_integer) 2);
  data->modelData->integerParameterData[7].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[10]] /* chamberR.pV.nout PARAM */) = ((modelica_integer) 1);
  data->modelData->integerParameterData[10].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[15]] /* command.nout PARAM */) = ((modelica_integer) 1);
  data->modelData->integerParameterData[15].time_unvarying = 1;
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* battery.rInt.T_ref PARAM */) = 300.15;
  data->modelData->realParameterData[6].time_unvarying = 1;
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[7]] /* battery.rInt.alpha PARAM */) = 0.0;
  data->modelData->realParameterData[7].time_unvarying = 1;
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[124]] /* command.timeScale PARAM */) = 1.0;
  data->modelData->realParameterData[124].time_unvarying = 1;
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[129]] /* motor.emf.fixed.phi0 PARAM */) = 0.0;
  data->modelData->realParameterData[129].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[0]] /* battery.rInt.useHeatPort PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[0].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[1]] /* chamberL.pV.isCsvExt PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[1].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[2]] /* chamberL.pV.tableOnFile PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[2].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[3]] /* chamberL.pV.verboseExtrapolation PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[3].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[4]] /* chamberL.pV.verboseRead PARAM */) = 1 /* true */;
  data->modelData->booleanParameterData[4].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[5]] /* chamberL.tableOnFile PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[5].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[6]] /* chamberR.pV.isCsvExt PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[6].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[7]] /* chamberR.pV.tableOnFile PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[7].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[8]] /* chamberR.pV.verboseExtrapolation PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[8].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[9]] /* chamberR.pV.verboseRead PARAM */) = 1 /* true */;
  data->modelData->booleanParameterData[9].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[10]] /* chamberR.tableOnFile PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[10].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[11]] /* command.isCsvExt PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[11].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[12]] /* command.tableOnFile PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[12].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[13]] /* command.verboseExtrapolation PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[13].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[15]] /* motor.emf.useSupport PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[15].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[16]] /* motor.friction.useHeatPort PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[16].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[17]] /* motor.resistor.useHeatPort PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[17].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[18]] /* pipeL.useInertance PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[18].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[19]] /* pipeR.useInertance PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[19].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[2]] /* chamberL.pV.extrapolation PARAM */) = 2;
  data->modelData->integerParameterData[2].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[5]] /* chamberL.pV.smoothness PARAM */) = 4;
  data->modelData->integerParameterData[5].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[8]] /* chamberR.pV.extrapolation PARAM */) = 2;
  data->modelData->integerParameterData[8].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[11]] /* chamberR.pV.smoothness PARAM */) = 4;
  data->modelData->integerParameterData[11].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[13]] /* command.extrapolation PARAM */) = 2;
  data->modelData->integerParameterData[13].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[16]] /* command.smoothness PARAM */) = 1;
  data->modelData->integerParameterData[16].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[18]] /* motor.friction.stateSelect PARAM */) = 4;
  data->modelData->integerParameterData[18].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[19]] /* motor.rotor.stateSelect PARAM */) = 3;
  data->modelData->integerParameterData[19].time_unvarying = 1;
  FishRobot_Examples_HydraulicsStep_updateBoundParameters_0(data, threadData);
  return 0;
}

#if defined(__cplusplus)
}
#endif
