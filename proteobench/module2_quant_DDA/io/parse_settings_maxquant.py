mapper = {
    "Raw file" : "Raw file",
    "Proteins" : "Proteins",
    "Modified sequence" : "Modified sequence",
    "Charge" : "Charge"
}

replicate_mapper = {
 'LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_01' : 1,
 'LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_02' : 1,
 'LFQ_Orbitrap_DDA_Condition_A_Sample_Alpha_03' : 1,
 'LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_01' : 2,
 'LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_02' : 2,
 'LFQ_Orbitrap_DDA_Condition_B_Sample_Alpha_03' : 2,
}

species_dict = {
    "YEAST" : "_YEAST",
    "ECOLI" : "_ECOLI",
    "HUMAN" : "_HUMAN"
}


species_expected_ratio = {
    "YEAST" : {"1|2" : 0.5},
    "ECOLI" : {"1|2" : 1.5},
    "HUMAN" : {"1|2" : 1.0}
}

contaminant_flag = "Cont_"
decoy_flag = True
min_count_multispec = 1