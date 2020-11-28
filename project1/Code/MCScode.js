var ldvalue = context.value;
// (a: b) means to set a to value b 
if (ldvalue > 50000)
    return {A_court_1: 1, A_court_1_occupy: 1};
else
    return {A_court_1: 0, A_court_1_occupy: 0};
