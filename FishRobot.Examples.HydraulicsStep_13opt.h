#if defined(__cplusplus)
  extern "C" {
#endif
  int FishRobot_Examples_HydraulicsStep_mayer(DATA* data, modelica_real** res, short*);
  int FishRobot_Examples_HydraulicsStep_lagrange(DATA* data, modelica_real** res, short *, short *);
  int FishRobot_Examples_HydraulicsStep_getInputVarIndicesInOptimization(DATA* data, int* input_var_indices);
  int FishRobot_Examples_HydraulicsStep_pickUpBoundsForInputsInOptimization(DATA* data, modelica_real* min, modelica_real* max, modelica_real*nominal, modelica_boolean *useNominal, char ** name, modelica_real * start, modelica_real * startTimeOpt);
  int FishRobot_Examples_HydraulicsStep_setInputData(DATA *data, const modelica_boolean file);
  int FishRobot_Examples_HydraulicsStep_getTimeGrid(DATA *data, modelica_integer * nsi, modelica_real**t);
#if defined(__cplusplus)
}
#endif
