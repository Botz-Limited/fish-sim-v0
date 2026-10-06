/* Initialization */
#include "FishRobot.Examples.HydraulicsStep_model.h"
#include "FishRobot.Examples.HydraulicsStep_11mix.h"
#include "FishRobot.Examples.HydraulicsStep_12jac.h"
#if defined(__cplusplus)
extern "C" {
#endif

void FishRobot_Examples_HydraulicsStep_functionInitialEquations_0(DATA *data, threadData_t *threadData);

/*
equation index: 1
type: SIMPLE_ASSIGN
motor.resistor.R_actual = motor.resistor.R * (1.0 + motor.resistor.alpha * (motor.resistor.T - motor.resistor.T_ref))
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_1(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,1};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[46]] /* motor.resistor.R_actual variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[136]] /* motor.resistor.R PARAM */)) * (1.0 + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[139]] /* motor.resistor.alpha PARAM */)) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[137]] /* motor.resistor.T PARAM */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[138]] /* motor.resistor.T_ref PARAM */)));
  threadData->lastEquationSolved = 1;
}

/*
equation index: 2
type: SIMPLE_ASSIGN
battery.rInt.R_actual = battery.rInt.R * (1.0 + battery.rInt.alpha * (battery.rInt.T - battery.rInt.T_ref))
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_2(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,2};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[25]] /* battery.rInt.R_actual variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[4]] /* battery.rInt.R PARAM */)) * (1.0 + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[7]] /* battery.rInt.alpha PARAM */)) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* battery.rInt.T PARAM */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* battery.rInt.T_ref PARAM */)));
  threadData->lastEquationSolved = 2;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_116(DATA *data, threadData_t *threadData);


/*
equation index: 4
type: SIMPLE_ASSIGN
command.nextTimeEventScaled = Modelica.Blocks.Tables.Internal.getNextTimeEvent(command.tableID, command.timeScaled)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_4(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,4};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[85]] /* command.nextTimeEventScaled DISCRETE */) = omc_Modelica_Blocks_Tables_Internal_getNextTimeEvent(threadData, (data->simulationInfo->extObjs[2]), (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[31]] /* command.timeScaled variable */));
  threadData->lastEquationSolved = 4;
}

/*
equation index: 5
type: SIMPLE_ASSIGN
command.nextTimeEvent = if command.nextTimeEventScaled < 1e60 then command.nextTimeEventScaled else 1e60
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_5(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,5};
  modelica_boolean tmp0;
  tmp0 = Less((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[85]] /* command.nextTimeEventScaled DISCRETE */),1e60);
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[84]] /* command.nextTimeEvent DISCRETE */) = (tmp0?(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[85]] /* command.nextTimeEventScaled DISCRETE */):1e60);
  threadData->lastEquationSolved = 5;
}

/*
equation index: 6
type: SIMPLE_ASSIGN
motor.inductor.i = $START.motor.inductor.i
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_6(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,6};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* motor.inductor.i STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[7] /* motor.inductor.i STATE(1) */).attribute .start.data))[0];
  threadData->lastEquationSolved = 6;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_112(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_109(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_110(DATA *data, threadData_t *threadData);


/*
equation index: 10
type: SIMPLE_ASSIGN
motor.rotor.w = $START.motor.rotor.w
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_10(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,10};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */) = ((modelica_real *)((data->modelData->realVarsData[52] /* motor.rotor.w DUMMY_STATE */).attribute .start.data))[0];
  threadData->lastEquationSolved = 10;
}

/*
equation index: 11
type: SIMPLE_ASSIGN
motor.friction.w_rel = -motor.rotor.w
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_11(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,11};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */) = (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */));
  threadData->lastEquationSolved = 11;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_115(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_113(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_114(DATA *data, threadData_t *threadData);


/*
equation index: 15
type: SIMPLE_ASSIGN
$DER.motor.rotor.phi = motor.rotor.w
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_15(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,15};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[17]] /* der(motor.rotor.phi) DUMMY_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */);
  threadData->lastEquationSolved = 15;
}

/*
equation index: 16
type: SIMPLE_ASSIGN
motor.emf.w = motor.rotor.w
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_16(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,16};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[42]] /* motor.emf.w variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */);
  threadData->lastEquationSolved = 16;
}

/*
equation index: 17
type: SIMPLE_ASSIGN
motor.emf.v = motor.emf.k * motor.emf.w
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_17(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,17};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[41]] /* motor.emf.v variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[130]] /* motor.emf.k PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[42]] /* motor.emf.w variable */));
  threadData->lastEquationSolved = 17;
}

/*
equation index: 18
type: SIMPLE_ASSIGN
$DER.motor.emf.phi = motor.emf.w
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_18(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,18};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[16]] /* der(motor.emf.phi) DUMMY_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[42]] /* motor.emf.w variable */);
  threadData->lastEquationSolved = 18;
}

/*
equation index: 19
type: SIMPLE_ASSIGN
$PRE.command.nextTimeEventScaled = 0.0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_19(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,19};
  (data->simulationInfo->realVarsPre[85] /* command.nextTimeEventScaled DISCRETE */) = 0.0;
  threadData->lastEquationSolved = 19;
}

/*
equation index: 20
type: SIMPLE_ASSIGN
command.y[1] = command.p_offset[1] + Modelica.Blocks.Tables.Internal.getTimeTableValueNoDer2(command.tableID, 1, command.timeScaled, command.nextTimeEventScaled, $PRE.command.nextTimeEventScaled)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_20(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,20};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[32]] /* command.y[1] variable */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[105]] /* command.p_offset[1] PARAM */) + omc_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer2(threadData, (data->simulationInfo->extObjs[2]), ((modelica_integer) 1), (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[31]] /* command.timeScaled variable */), (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[85]] /* command.nextTimeEventScaled DISCRETE */), (data->simulationInfo->realVarsPre[85] /* command.nextTimeEventScaled DISCRETE */));
  threadData->lastEquationSolved = 20;
}

/*
equation index: 21
type: SIMPLE_ASSIGN
bridge.u_lim = max(-1.0, min(1.0, command.y[1]))
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_21(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,21};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[29]] /* bridge.u_lim variable */) = fmax(-1.0,fmin(1.0,(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[32]] /* command.y[1] variable */)));
  threadData->lastEquationSolved = 21;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_123(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_124(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_125(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_126(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_127(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_128(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_129(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_130(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_134(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_131(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_132(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_133(DATA *data, threadData_t *threadData);


/*
equation index: 34
type: SIMPLE_ASSIGN
chamberL.V = chamberL.V_prefill
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_34(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,34};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* chamberL.V STATE(1,pipeL.V_flow) */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[8]] /* chamberL.V_prefill PARAM */);
  threadData->lastEquationSolved = 34;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_140(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_141(DATA *data, threadData_t *threadData);


/*
equation index: 37
type: SIMPLE_ASSIGN
chamberR.V = chamberR.V_prefill
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_37(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,37};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[4]] /* chamberR.V STATE(1,pipeR.V_flow) */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[56]] /* chamberR.V_prefill PARAM */);
  threadData->lastEquationSolved = 37;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_138(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_139(DATA *data, threadData_t *threadData);


void FishRobot_Examples_HydraulicsStep_eqFunction_40(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_41(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_42(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_43(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_44(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_45(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_46(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_47(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_48(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_49(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_50(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_53(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_52(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_51(DATA*, threadData_t*);
/*
equation index: 67
indexNonlinear: 0
type: NONLINEAR

vars: {pipeR.V_flow, reliefRL.dp, reliefLR.dp}
eqns: {40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 53, 52, 51}
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_67(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,67};
  int retValue;
  infoStreamPrint(OMC_LOG_DT, 0, "Solving nonlinear system 67 (STRICT TEARING SET if tearing enabled) at time = %18.10e", data->localData[0]->timeValue);
  /* get old value */
  data->simulationInfo->nonlinearSystemData[0].nlsxOld[0] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  data->simulationInfo->nonlinearSystemData[0].nlsxOld[1] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */);
  data->simulationInfo->nonlinearSystemData[0].nlsxOld[2] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */);
  retValue = solve_nonlinear_system(data, threadData, 0);
  /* check if solution process was successful */
  if (retValue > 0){
    const int indexes[2] = {1,67};
    throwStreamPrintWithEquationIndexes(threadData, omc_dummyFileInfo, indexes, "Solving non-linear system 67 failed at time=%.15g.\nFor more information please use -lv LOG_NLS.", data->localData[0]->timeValue);
  }
  /* write solution */
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */) = data->simulationInfo->nonlinearSystemData[0].nlsx[0];
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) = data->simulationInfo->nonlinearSystemData[0].nlsx[1];
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) = data->simulationInfo->nonlinearSystemData[0].nlsx[2];
  threadData->lastEquationSolved = 67;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_187(DATA *data, threadData_t *threadData);


/*
equation index: 69
type: SIMPLE_ASSIGN
pump.tau_fric = pump.D * abs(pump.dp_pump) * (-1.0 + 1.0 / pump.eta_m) * motor.rotor.w / sqrt(motor.rotor.w ^ 2.0 + pump.w_small ^ 2.0)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_69(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,69};
  modelica_real tmp1;
  modelica_real tmp2;
  modelica_real tmp3;
  tmp1 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */);
  tmp2 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[168]] /* pump.w_small PARAM */);
  tmp3 = (tmp1 * tmp1) + (tmp2 * tmp2);
  if(!(tmp3 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(motor.rotor.w ^ 2.0 + pump.w_small ^ 2.0) was %g should be >= 0", tmp3);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[73]] /* pump.tau_fric variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[164]] /* pump.D PARAM */)) * ((fabs((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */))) * ((-1.0 + DIVISION_SIM(1.0,(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[166]] /* pump.eta_m PARAM */),"pump.eta_m",equationIndexes)) * (DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */),sqrt(tmp3),"sqrt(motor.rotor.w ^ 2.0 + pump.w_small ^ 2.0)",equationIndexes))));
  threadData->lastEquationSolved = 69;
}

/*
equation index: 70
type: SIMPLE_ASSIGN
pump.P_loss_mech = pump.tau_fric * motor.rotor.w
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_70(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,70};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[69]] /* pump.P_loss_mech variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[73]] /* pump.tau_fric variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */));
  threadData->lastEquationSolved = 70;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_180(DATA *data, threadData_t *threadData);


/*
equation index: 72
type: SIMPLE_ASSIGN
pump.P_shaft = pump.flange.tau * motor.rotor.w
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_72(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,72};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[70]] /* pump.P_shaft variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[72]] /* pump.flange.tau variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */));
  threadData->lastEquationSolved = 72;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_182(DATA *data, threadData_t *threadData);


/*
equation index: 74
type: SIMPLE_ASSIGN
motor.rotor.a = (motor.rotor.flange_b.tau - motor.emf.tau) / motor.rotor.J
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_74(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,74};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[49]] /* motor.rotor.a variable */) = DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[50]] /* motor.rotor.flange_b.tau variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[40]] /* motor.emf.tau variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[140]] /* motor.rotor.J PARAM */),"motor.rotor.J",equationIndexes);
  threadData->lastEquationSolved = 74;
}

/*
equation index: 75
type: SIMPLE_ASSIGN
motor.friction.a_rel = -motor.rotor.a
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_75(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,75};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[43]] /* motor.friction.a_rel variable */) = (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[49]] /* motor.rotor.a variable */));
  threadData->lastEquationSolved = 75;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_184(DATA *data, threadData_t *threadData);


/*
equation index: 77
type: SIMPLE_ASSIGN
$DER.motor.rotor.w = motor.rotor.a
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_77(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,77};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[18]] /* der(motor.rotor.w) DUMMY_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[49]] /* motor.rotor.a variable */);
  threadData->lastEquationSolved = 77;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_188(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_172(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_171(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_193(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_191(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_189(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_190(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_192(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_170(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_176(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_175(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_173(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_174(DATA *data, threadData_t *threadData);

extern void FishRobot_Examples_HydraulicsStep_eqFunction_177(DATA *data, threadData_t *threadData);


/*
equation index: 92
type: SIMPLE_ASSIGN
ground.p.v = 0.0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_92(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,92};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[34]] /* ground.p.v variable */) = 0.0;
  threadData->lastEquationSolved = 92;
}

/*
equation index: 93
type: SIMPLE_ASSIGN
$PRE.command.nextTimeEvent = 0.0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_93(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,93};
  (data->simulationInfo->realVarsPre[84] /* command.nextTimeEvent DISCRETE */) = 0.0;
  threadData->lastEquationSolved = 93;
}

/*
equation index: 94
type: SIMPLE_ASSIGN
$whenCondition1 = time >= $PRE.command.nextTimeEvent
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_94(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,94};
  modelica_boolean tmp4;
  tmp4 = GreaterEq(data->localData[0]->timeValue,(data->simulationInfo->realVarsPre[84] /* command.nextTimeEvent DISCRETE */));
  (data->localData[0]->booleanVars[data->simulationInfo->booleanVarsIndex[0]] /* $whenCondition1 DISCRETE */) = tmp4;
  threadData->lastEquationSolved = 94;
}

/*
equation index: 95
type: SIMPLE_ASSIGN
motor.rotor.phi = $START.motor.rotor.phi
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_95(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,95};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[51]] /* motor.rotor.phi DUMMY_STATE */) = ((modelica_real *)((data->modelData->realVarsData[51] /* motor.rotor.phi DUMMY_STATE */).attribute .start.data))[0];
  threadData->lastEquationSolved = 95;
}

/*
equation index: 96
type: SIMPLE_ASSIGN
motor.friction.phi_rel = motor.housing.phi0 - motor.rotor.phi
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_96(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,96};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[5]] /* motor.friction.phi_rel STATE(1,motor.friction.w_rel) */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[133]] /* motor.housing.phi0 PARAM */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[51]] /* motor.rotor.phi DUMMY_STATE */);
  threadData->lastEquationSolved = 96;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_137(DATA *data, threadData_t *threadData);


/*
equation index: 98
type: SIMPLE_ASSIGN
battery.E_drawn = $START.battery.E_drawn
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_98(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,98};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* battery.E_drawn STATE(1,battery.P_chem) */) = ((modelica_real *)((data->modelData->realVarsData[0] /* battery.E_drawn STATE(1,battery.P_chem) */).attribute .start.data))[0];
  threadData->lastEquationSolved = 98;
}

/*
equation index: 99
type: SIMPLE_ASSIGN
chamberL.E_elastic = $START.chamberL.E_elastic
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_99(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,99};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[1]] /* chamberL.E_elastic STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[1] /* chamberL.E_elastic STATE(1) */).attribute .start.data))[0];
  threadData->lastEquationSolved = 99;
}

/*
equation index: 100
type: SIMPLE_ASSIGN
chamberR.E_elastic = $START.chamberR.E_elastic
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_100(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,100};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* chamberR.E_elastic STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[3] /* chamberR.E_elastic STATE(1) */).attribute .start.data))[0];
  threadData->lastEquationSolved = 100;
}
extern void FishRobot_Examples_HydraulicsStep_eqFunction_104(DATA *data, threadData_t *threadData);


/*
equation index: 103
type: ALGORITHM

  assert(1.0 + motor.resistor.alpha * (motor.resistor.T - motor.resistor.T_ref) >= 2.220446049250313e-16, "Temperature outside scope of model!");
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_103(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,103};
  modelica_boolean tmp5;
  static const MMC_DEFSTRINGLIT(tmp6,35,"Temperature outside scope of model!");
  static int tmp7 = 0;
  {
    tmp5 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[139]] /* motor.resistor.alpha PARAM */)) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[137]] /* motor.resistor.T PARAM */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[138]] /* motor.resistor.T_ref PARAM */)),2.220446049250313e-16);
    if(!tmp5)
    {
      {
        const char* assert_cond = "(1.0 + motor.resistor.alpha * (motor.resistor.T - motor.resistor.T_ref) >= 2.220446049250313e-16)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp6)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp6)));
        }
      }
    }
  }
  threadData->lastEquationSolved = 103;
}

/*
equation index: 102
type: ALGORITHM

  assert(1.0 + battery.rInt.alpha * (battery.rInt.T - battery.rInt.T_ref) >= 2.220446049250313e-16, "Temperature outside scope of model!");
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_102(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,102};
  modelica_boolean tmp8;
  static const MMC_DEFSTRINGLIT(tmp9,35,"Temperature outside scope of model!");
  static int tmp10 = 0;
  {
    tmp8 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[7]] /* battery.rInt.alpha PARAM */)) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* battery.rInt.T PARAM */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* battery.rInt.T_ref PARAM */)),2.220446049250313e-16);
    if(!tmp8)
    {
      {
        const char* assert_cond = "(1.0 + battery.rInt.alpha * (battery.rInt.T - battery.rInt.T_ref) >= 2.220446049250313e-16)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp9)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp9)));
        }
      }
    }
  }
  threadData->lastEquationSolved = 102;
}
OMC_DISABLE_OPT
void FishRobot_Examples_HydraulicsStep_functionInitialEquations_0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[76])(DATA*, threadData_t*) = {
    FishRobot_Examples_HydraulicsStep_eqFunction_1,
    FishRobot_Examples_HydraulicsStep_eqFunction_2,
    FishRobot_Examples_HydraulicsStep_eqFunction_116,
    FishRobot_Examples_HydraulicsStep_eqFunction_4,
    FishRobot_Examples_HydraulicsStep_eqFunction_5,
    FishRobot_Examples_HydraulicsStep_eqFunction_6,
    FishRobot_Examples_HydraulicsStep_eqFunction_112,
    FishRobot_Examples_HydraulicsStep_eqFunction_109,
    FishRobot_Examples_HydraulicsStep_eqFunction_110,
    FishRobot_Examples_HydraulicsStep_eqFunction_10,
    FishRobot_Examples_HydraulicsStep_eqFunction_11,
    FishRobot_Examples_HydraulicsStep_eqFunction_115,
    FishRobot_Examples_HydraulicsStep_eqFunction_113,
    FishRobot_Examples_HydraulicsStep_eqFunction_114,
    FishRobot_Examples_HydraulicsStep_eqFunction_15,
    FishRobot_Examples_HydraulicsStep_eqFunction_16,
    FishRobot_Examples_HydraulicsStep_eqFunction_17,
    FishRobot_Examples_HydraulicsStep_eqFunction_18,
    FishRobot_Examples_HydraulicsStep_eqFunction_19,
    FishRobot_Examples_HydraulicsStep_eqFunction_20,
    FishRobot_Examples_HydraulicsStep_eqFunction_21,
    FishRobot_Examples_HydraulicsStep_eqFunction_123,
    FishRobot_Examples_HydraulicsStep_eqFunction_124,
    FishRobot_Examples_HydraulicsStep_eqFunction_125,
    FishRobot_Examples_HydraulicsStep_eqFunction_126,
    FishRobot_Examples_HydraulicsStep_eqFunction_127,
    FishRobot_Examples_HydraulicsStep_eqFunction_128,
    FishRobot_Examples_HydraulicsStep_eqFunction_129,
    FishRobot_Examples_HydraulicsStep_eqFunction_130,
    FishRobot_Examples_HydraulicsStep_eqFunction_134,
    FishRobot_Examples_HydraulicsStep_eqFunction_131,
    FishRobot_Examples_HydraulicsStep_eqFunction_132,
    FishRobot_Examples_HydraulicsStep_eqFunction_133,
    FishRobot_Examples_HydraulicsStep_eqFunction_34,
    FishRobot_Examples_HydraulicsStep_eqFunction_140,
    FishRobot_Examples_HydraulicsStep_eqFunction_141,
    FishRobot_Examples_HydraulicsStep_eqFunction_37,
    FishRobot_Examples_HydraulicsStep_eqFunction_138,
    FishRobot_Examples_HydraulicsStep_eqFunction_139,
    FishRobot_Examples_HydraulicsStep_eqFunction_67,
    FishRobot_Examples_HydraulicsStep_eqFunction_187,
    FishRobot_Examples_HydraulicsStep_eqFunction_69,
    FishRobot_Examples_HydraulicsStep_eqFunction_70,
    FishRobot_Examples_HydraulicsStep_eqFunction_180,
    FishRobot_Examples_HydraulicsStep_eqFunction_72,
    FishRobot_Examples_HydraulicsStep_eqFunction_182,
    FishRobot_Examples_HydraulicsStep_eqFunction_74,
    FishRobot_Examples_HydraulicsStep_eqFunction_75,
    FishRobot_Examples_HydraulicsStep_eqFunction_184,
    FishRobot_Examples_HydraulicsStep_eqFunction_77,
    FishRobot_Examples_HydraulicsStep_eqFunction_188,
    FishRobot_Examples_HydraulicsStep_eqFunction_172,
    FishRobot_Examples_HydraulicsStep_eqFunction_171,
    FishRobot_Examples_HydraulicsStep_eqFunction_193,
    FishRobot_Examples_HydraulicsStep_eqFunction_191,
    FishRobot_Examples_HydraulicsStep_eqFunction_189,
    FishRobot_Examples_HydraulicsStep_eqFunction_190,
    FishRobot_Examples_HydraulicsStep_eqFunction_192,
    FishRobot_Examples_HydraulicsStep_eqFunction_170,
    FishRobot_Examples_HydraulicsStep_eqFunction_176,
    FishRobot_Examples_HydraulicsStep_eqFunction_175,
    FishRobot_Examples_HydraulicsStep_eqFunction_173,
    FishRobot_Examples_HydraulicsStep_eqFunction_174,
    FishRobot_Examples_HydraulicsStep_eqFunction_177,
    FishRobot_Examples_HydraulicsStep_eqFunction_92,
    FishRobot_Examples_HydraulicsStep_eqFunction_93,
    FishRobot_Examples_HydraulicsStep_eqFunction_94,
    FishRobot_Examples_HydraulicsStep_eqFunction_95,
    FishRobot_Examples_HydraulicsStep_eqFunction_96,
    FishRobot_Examples_HydraulicsStep_eqFunction_137,
    FishRobot_Examples_HydraulicsStep_eqFunction_98,
    FishRobot_Examples_HydraulicsStep_eqFunction_99,
    FishRobot_Examples_HydraulicsStep_eqFunction_100,
    FishRobot_Examples_HydraulicsStep_eqFunction_104,
    FishRobot_Examples_HydraulicsStep_eqFunction_103,
    FishRobot_Examples_HydraulicsStep_eqFunction_102
  };
  
  for (int id = 0; id < 76; id++) {
    eqFunctions[id](data, threadData);
  }
}

int FishRobot_Examples_HydraulicsStep_functionInitialEquations(DATA *data, threadData_t *threadData)
{
  data->simulationInfo->discreteCall = 1;
  FishRobot_Examples_HydraulicsStep_functionInitialEquations_0(data, threadData);
  data->simulationInfo->discreteCall = 0;
  
  return 0;
}

/* No FishRobot_Examples_HydraulicsStep_functionInitialEquations_lambda0 function */

int FishRobot_Examples_HydraulicsStep_functionRemovedInitialEquations(DATA *data, threadData_t *threadData)
{
  const int *equationIndexes = NULL;
  double res = 0.0;

  
  return 0;
}


#if defined(__cplusplus)
}
#endif
