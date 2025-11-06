import subprocess


# Protein Hunter (Boltz Edition ⚡) 
# protein binding design
cmd = [
    "python", "boltz_ph/design.py",
    "--num_designs", "2",
    "--num_cycles", "7",
    "--protein_seqs", "AFTVTVPKDLYVVEYGSNMTIECKFPVEKQLDLAALIVYWEMEDKNIIQFVHGEEDLKVQHSSYRQRARLLKDQLSLGNAALQITDVKLQDAGVYRCMISYGGADYKRITVKVNAPYAAALE",
    "--protein_ids", "B",
    "--protein_msas", "",
    "--gpu_id", "2",
    "--name", "PDL1_mix_aa_v2",
    "--min_design_protein_length", "90",
    "--max_design_protein_length", "150",
    "--high_iptm_threshold", "0.7",
    "--use_msa_for_af3",
    "--plot"
]
subprocess.run(cmd, check=True)

cmd = [
    "python", "boltz_ph/design.py",
    "--num_designs", "3",
    "--num_cycles", "7",
    "--protein_seqs", "FTVTVPKDLYVVEYGSNMTIECKFPVEKQLDLAALIVYWEMEDKNIIQFVHGEEDLKVQHSSYRQRARLLKDQLSLGNAALQITDVKLQDAGVYRCMISYGGADYKRITVKVNK",
    "--protein_ids", "B",
    "--protein_msas", "empty",
    "--gpu_id", "1",
    "--name", "PDL1_mix_aa_template",
    "--template_path", "8ZNL",
    "--template_chain_id", "B",
    "--template_cif_chain_id", "B",
    "--min_design_protein_length", "90",
    "--max_design_protein_length", "150",
    "--high_iptm_threshold", "0.7",
    "--use_msa_for_af3",
    "--plot"
]
subprocess.run(cmd, check=True)

#multimer binding design
cmd = [
    "python", "boltz_ph/design.py",
    "--num_designs", "3",
    "--num_cycles", "7",
    "--protein_seqs", "AFTVTVPKDLYVVEYGSNMTIECKFPVEKQLDLAALIVYWEMEDKNIIQFVHGEEDLKVQHSSYRQRARLLKDQLSLGNAALQITDVKLQDAGVYRCMISYGGADYKRITVKVNAPYAAALE:AFTVTVPKDLYVVEYGSNMTIECKFPVEKQLDLAALIVYWEMEDKNIIQFVHGEEDLKVQHSSYRQRARLLKDQLSLGNAALQITDVKLQDAGVYRCMISYGGADYKRITVKVNAPYAAALE",
    "--protein_ids", "B:C",
    "--protein_msas", "",
    "--gpu_id", "2",
    "--name", "PDL1_double_mix_aa_v2",
    "--min_design_protein_length", "90",
    "--max_design_protein_length", "150",
    "--high_iptm_threshold", "0.7",
    "--use_msa_for_af3",
    "--plot"
]
subprocess.run(cmd, check=True)

#protein binder with contact residues
cmd = [
    "python", "boltz_ph/design.py",
    "--num_designs", "3",
    "--num_cycles", "7",
    "--protein_seqs", "AFTVTVPKDLYVVEYGSNMTIECKFPVEKQLDLAALIVYWEMEDKNIIQFVHGEEDLKVQHSSYRQRARLLKDQLSLGNAALQITDVKLQDAGVYRCMISYGGADYKRITVKVNAPYAAALE",
    "--protein_ids", "B",
    "--protein_msas", "",
    "--gpu_id", "2",
    "--contact_residues", "29,277,279,293,294,295,318,319,320,371",
    "--add_constraints",
    "--name", "PDL1_contact_residues_mix_aa",
    "--min_design_protein_length", "90",
    "--max_design_protein_length", "150",
    "--high_iptm_threshold", "0.7",
    "--use_msa_for_af3",
    "--plot"
]
subprocess.run(cmd, check=True)

# #protein + small molecule binding design
cmd = [
    "python", "boltz_ph/design.py",
    "--num_designs", "3",
    "--num_cycles", "7",
    "--protein_seqs", "AFTVTVPKDLYVVEYGSNMTIECKFPVEKQLDLAALIVYWEMEDKNIIQFVHGEEDLKVQHSSYRQRARLLKDQLSLGNAALQITDVKLQDAGVYRCMISYGGADYKRITVKVNAPYAAALE",
    "--protein_ids", "B",
    "--protein_msas", "",
    "--gpu_id", "2",
    "--name", "PDL1_SAM_mix_aa",
    "--ligand_ccd", "SAM",
    "--ligand_id", "C",
    "--min_design_protein_length", "90",
    "--max_design_protein_length", "150",
    "--high_iptm_threshold", "0.7",
    "--use_msa_for_af3",
    "--plot"
]
subprocess.run(cmd, check=True)


#nucleic acid binding design
cmd = [
    "python", "boltz_ph/design.py",
    "--num_designs", "3",
    "--num_cycles", "7",
    "--gpu_id", "2",
    "--name", "rna_mix_aa_v2",
    "--nucleic_seq", "AGAGAGA",
    "--nucleic_type", "rna",
    "--nucleic_id", "C",
    "--min_design_protein_length", "90",
    "--max_design_protein_length", "150",
    "--high_iptm_threshold", "0.7",
    "--use_msa_for_af3",
    "--plot"
]
subprocess.run(cmd, check=True)




#Protein Hunter (Chai Edition ☕)

#unconditional design
cmd = [
    "python", "chai_ph/design.py",
    "--jobname", "unconditional_design",
    "--length", "120",
    "--percent_X", "0",
    "--seq", "",
    "--cyclic",
    "--n_trials", "3",
    "--n_cycles", "7",
    "--n_recycles", "3",
    "--n_diff_steps", "200",
    "--hysteresis_mode", "templates",
    "--repredict",
    "--omit_aa", "",
    "--temperature", "0.1",
    "--scale_temp_by_plddt",
    "--render_freq", "100",
    "--gpu_id", "2",
]
subprocess.run(cmd, check=True)

#unconditional design
cmd = [
    "python", "chai_ph/design.py",
    "--jobname", "unconditional_design_negative_alanine_bias",
    "--length", "200",
    "--percent_X", "0",
    "--seq", "",
    "--cyclic",
    "--n_trials", "1",
    "--n_cycles", "5",
    "--n_recycles", "3",
    "--n_diff_steps", "200",
    "--hysteresis_mode", "templates",
    "--repredict",
    "--omit_aa", "",
    "--bias_aa", "A:-0.5",
    "--temperature", "0.1",
    "--scale_temp_by_plddt",
    "--render_freq", "100",
    "--gpu_id", "2",
]
subprocess.run(cmd, check=True)

#protein binder design
cmd = [
    "python", "chai_ph/design.py",
    "--jobname", "PDL1_binder",
    "--length", "120",
    "--percent_X", "50",
    "--seq", "",
    "--target_seq", "AFTVTVPKDLYVVEYGSNMTIECKFPVEKQLDLAALIVYWEMEDKNIIQFVHGEEDLKVQHSSYRQRARLLKDQLSLGNAALQITDVKLQDAGVYRCMISYGGADYKRITVKVNAPYAAALE",
    "--n_trials", "3",
    "--n_cycles", "7",
    "--n_recycles", "3",
    "--n_diff_steps", "200",
    "--hysteresis_mode", "templates",
    "--repredict",
    "--omit_aa", "",
    "--temperature", "0.1",
    "--scale_temp_by_plddt",
    "--render_freq", "100",
    "--gpu_id", "2",
    "--use_msa_for_af3",
]
subprocess.run(cmd, check=True)


#protein cyclic binder design

cmd = [
    "python", "chai_ph/design.py",
    "--jobname", "PDL1_cyclic_binder",
    "--length", "15",
    "--percent_X", "50",
    "--seq", "",
    "--cyclic",
    "--target_seq", "AFTVTVPKDLYVVEYGSNMTIECKFPVEKQLDLAALIVYWEMEDKNIIQFVHGEEDLKVQHSSYRQRARLLKDQLSLGNAALQITDVKLQDAGVYRCMISYGGADYKRITVKVNAPYAAALE",
    "--n_trials", "3",
    "--n_cycles", "7",
    "--n_recycles", "3",
    "--n_diff_steps", "200",
    "--hysteresis_mode", "templates",
    "--repredict",
    "--omit_aa", "",
    "--temperature", "0.1",
    "--scale_temp_by_plddt",
    "--render_freq", "100",
    "--gpu_id", "2",
    "--use_msa_for_af3",
]
subprocess.run(cmd, check=True)


#ligand binder design
cmd = [
    "python", "chai_ph/design.py",
    "--jobname", "ligand_binder",
    "--length", "120",
    "--percent_X", "50",
    "--seq", "",
    "--target_seq", "O=C(NCc1cocn1)c1cnn(C)c1C(=O)Nc1ccn2cc(nc2n1)c1ccccc1",
    "--n_trials", "3",
    "--n_cycles", "7",
    "--n_recycles", "3",
    "--n_diff_steps", "200",
    "--hysteresis_mode", "esm",
    "--repredict",
    "--omit_aa", "",
    "--temperature", "0.01",
    "--scale_temp_by_plddt",
    "--render_freq", "100",
    "--gpu_id", "2",
]
subprocess.run(cmd, check=True)