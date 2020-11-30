// take A_ldr_1's code for example, there's same logic in A_ldr_2, 3, 4
var ldvalue = context.value;
if (ldvalue > 50000)
    return { A_court_1: 1, A_court_1_occupy: 1 };
else
    return { A_court_1: 0, A_court_1_occupy: 0 };