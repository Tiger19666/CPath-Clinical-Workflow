import subprocess
from pathlib import Path
import sys, tempfile, pandas as pd, yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from modules.router.route_request import route
from modules.splits.build_group_split import build
from modules.representation.route_representation import route as rep_route
from modules.models.route_downstream import route as model_route
from modules.execution.resolve_execution_permission import resolve
from modules.execution.build_dependency_dag import build as dag_build
from modules.handoff.build_autoresearch_handoff import build as handoff_build
from modules.tasks.build_portfolio import build as portfolio_build
from modules.readiness.assess_task_readiness import assess as readiness_assess

def test_modes():
    assert route({'requested_tasks':[]})['mode']=='DISCOVERY'
    assert route({'requested_tasks':['HER2']})['mode']=='TASK_SPECIFIED'
    assert route({'requested_tasks':['ER','PR']})['mode']=='MULTI_TASK_SPECIFIED'

def test_discovery_not_auto_execute():
    r=route({'requested_tasks':[]})
    assert r['execution_intent']=='ASSESS_ONLY'
    assert not resolve(r['mode'],r['execution_intent'],'READY_TO_RUN')['allowed']

def test_specified_execute_can_run():
    r=route({'requested_tasks':['HER2'],'execution_intent':'EXECUTE'})
    assert resolve(r['mode'],r['execution_intent'],'READY_TO_RUN')['allowed']

def test_group_split_has_no_group_overlap():
    df=pd.DataFrame({'patient':['p1','p1','p2','p3','p4','p5','p6','p7','p8','p9'],'label':[0,0,1,0,1,0,1,0,1,0]})
    out,s=build(df,'patient','label',seed=1)
    assert all(v==0 for v in s['group_overlap'].values())
    by=out.groupby('patient')['split'].nunique()
    assert by.max()==1

def test_representation_routes():
    assert rep_route({'task_id':'1','task_family':'vqa','required_modalities':['WSI','text']})['route']=='VISION_LANGUAGE'
    x=rep_route({'task_id':'2','task_family':'classification','required_modalities':['WSI'],'optional_modalities':['clinical']})
    assert x['route']=='VISION'
    assert 'MULTIMODAL' in x['comparison_routes']
    assert rep_route({'task_id':'3','task_family':'segmentation','required_modalities':['ROI']})['route']=='DENSE_VISION'

def test_standard_baselines_no_novelty():
    x=model_route({'task_id':'T','task_family':'classification'})
    assert 'abmil' in x['standard_baselines']
    assert x['novel_algorithm_allowed_here'] is False

def test_multitask_dag_shares_representation():
    d=dag_build([{'task_id':'ER','representation_key':'UNI2_A'},{'task_id':'PR','representation_key':'UNI2_A'},{'task_id':'SEG','representation_key':'DENSE_B'}])
    assert set(d['shared_representation_groups']['UNI2_A'])=={'ER','PR'}

def test_handoff_freezes_clinical_contract():
    h=handoff_build({'task_id':'T1','target':'HER2','label_definition':'binary','clinical_question':'Can H&E predict HER2?','prediction_level':'patient','task_family':'classification'}, {'test_manifest':'test.csv'}, {'encoder':'UNI2'}, {'ABMIL':{'auc':0.8}}, {'maximum_claim_level':'EXECUTION_ONLY'})
    assert h['status']=='NOT_READY'
    assert h['immutable']['clinical_endpoint']=='HER2'
    assert 'clinical_endpoint' in h['forbidden_changes']


def test_portfolio_retains_all_labels_and_no_single_winner():
    p=portfolio_build({'labels':[
      {'label_id':'L1','name':'HER2','semantic_role':'biomarker','level':'patient','coverage':0.9,'quality':'SILVER','linkage_status':'VERIFIED'},
      {'label_id':'L2','name':'OS','semantic_role':'overall_survival','level':'patient','coverage':0.1,'quality':'SILVER','linkage_status':'VERIFIED'},
      {'label_id':'L3','name':'Grade','semantic_role':'grade','level':'patient','coverage':0.8,'quality':'SILVER','linkage_status':'FAILED'},
    ]})
    assert p['portfolio_size']==3
    assert p['selection_policy']=='retain_all_candidates'
    assert [x['status'] for x in p['tasks']]==['GO','CONDITIONAL_GO','NO_GO']

def test_readiness_separates_task_and_environment():
    t={'task_id':'T1','status':'GO','dependencies':[]}
    assert readiness_assess(t,True,True)['readiness']=='READY_TO_RUN'
    assert readiness_assess(t,True,False)['readiness']=='CONDITIONAL_READY'

from modules.task_validation.validate_task_spec import validate as validate_task
from modules.clinical_literature.build_search_plan import build as literature_plan_build
from modules.clinical_literature.validate_search_coverage import validate as literature_coverage_validate
from modules.clinical_literature.verify_bibliography import verify as bibliography_verify
from modules.clinical_literature.build_clinical_landscape import build as landscape_build
from modules.clinical_literature.assess_clinical_gap import assess as gap_assess
from modules.features.classify_feature_provenance import classify as classify_feature_provenance


def test_task_semantics_reject_segmentation_patient_level():
    x=validate_task({'task_id':'T16','name':'seg','clinical_question':'Can lesions be segmented?','task_family':'segmentation','prediction_level':'patient','target':'tumor_mask','label_source':'mask'})
    assert x['status']=='FAIL'
    assert 'prediction_level_incompatible_with_segmentation' in x['errors']


def test_task_semantics_reject_non_atomic_target():
    x=validate_task({'task_id':'T14','name':'mixed','clinical_question':'Can this be predicted?','task_family':'classification','prediction_level':'patient','target':'report generation or VQA','label_source':'mixed'})
    assert x['status']=='FAIL'
    assert 'non_atomic_target' in x['errors']


def test_clinical_literature_plan_has_four_required_families():
    p=literature_plan_build({'task_id':'T1','target':'HER2','name':'HER2 prediction','clinical_question':'Can H&E predict HER2?','disease_context':'breast cancer'})
    assert len(p['required_query_families'])==4
    assert p['completion_rule']['requires_real_search_trace'] is True


def test_literature_coverage_cannot_self_declare_complete():
    trace={'task_id':'T1','status':'COMPLETE','searches':[
      {'family':'clinical_endpoint','query':'q','source':'PubMed','executed':False,'results_screened':10,'selected_reference_ids':['L1']}
    ]}
    c=literature_coverage_validate(trace)
    assert c['status']=='INCOMPLETE'


def test_bibliography_requires_external_resolver_and_detects_mismatch():
    no_external=bibliography_verify({'task_id':'T1','references':[{
      'reference_id':'L1','claimed':{'title':'Same fake title','year':2024},'resolved':{'title':'Same fake title','year':2024},'evidence_roles':['pathology_ai']
    }]})
    assert no_external['references'][0]['verification_status']=='UNRESOLVED'
    mismatch=bibliography_verify({'task_id':'T1','references':[{
      'reference_id':'L2','claimed':{'title':'Wrong title','year':2024},'resolved':{'resolver':'pubmed','title':'Completely different real title','year':2024,'source_url':'https://pubmed.ncbi.nlm.nih.gov/123','resolver_record_id':'PMID:123'},'evidence_roles':['pathology_ai']
    }]})
    assert mismatch['references'][0]['verification_status']=='MISMATCH'


def test_incomplete_literature_downgrades_go():
    task={'task_id':'T1','status':'GO','clinical_question':'Can H&E predict HER2?'}
    cov={'status':'INCOMPLETE','clinical_gap_confidence_ceiling':'MEDIUM'}
    land={'evidence_role_counts':{}}
    g=gap_assess(task,cov,land)
    assert g['recommended_task_status']=='CONDITIONAL_GO'


def test_unknown_legacy_features_are_reference_only():
    x=classify_feature_provenance({'exists':True,'file_count':100,'feature_dimension':1024})
    assert x['provenance_class']=='LEGACY_FEATURE_PROVENANCE_INCOMPLETE'
    assert x['reuse_status']=='QUICK_REFERENCE_ONLY'


def test_known_fm_feature_requires_provenance_contract():
    x=classify_feature_provenance({'exists':True,'file_count':100,'source_type':'foundation_model','encoder':'UNI2','encoder_version':'v1','preprocessing_contract':{'patch_size':224}})
    assert x['provenance_class']=='KNOWN_FM_FEATURE'
    assert x['reuse_status']=='PRIMARY_REPRODUCIBLE'


def test_representation_router_distinguishes_legacy_from_known_fm():
    task={'task_id':'T1','task_family':'classification','required_modalities':['WSI']}
    legacy=rep_route(task,{'provenance_class':'LEGACY_FEATURE_PROVENANCE_INCOMPLETE'})
    known=rep_route(task,{'provenance_class':'KNOWN_FM_FEATURE','reuse_status':'PRIMARY_REPRODUCIBLE'})
    assert legacy['representation_strategy']=='REUSE_LEGACY_FEATURES_FOR_REFERENCE_ONLY'
    assert known['representation_strategy']=='REUSE_KNOWN_FM_FEATURES'


def test_survival_clinical_baseline_contract_has_three_comparators():
    x=model_route({'task_id':'T5','task_family':'survival','required_modalities':['WSI'],'optional_modalities':['clinical']})
    groups={g['group'] for g in x['baseline_comparison_contract']}
    assert {'pathology_only','clinical_only','pathology_plus_clinical'} <= groups


def test_dag_does_not_duplicate_rep_prefix():
    d=dag_build([{'task_id':'ER','representation_key':'REP::UNI2_A'}])
    ids={n['id'] for n in d['nodes']}
    assert 'REP::UNI2_A' in ids
    assert 'REP::REP::UNI2_A' not in ids


def test_future_opportunities_are_separate_from_supported_tasks():
    p=portfolio_build({'labels':[
      {'label_id':'L1','name':'HER2','semantic_role':'biomarker','level':'patient','coverage':0.9,'quality':'SILVER','linkage_status':'VERIFIED'},
      {'label_id':'L2','name':'Recurrence','semantic_role':'recurrence','level':'patient','locally_supported':False,'unsupported_reason':'no recurrence endpoint'},
    ]})
    assert p['portfolio_size']==1
    assert p['future_opportunity_count']==1


def test_bibliography_verifies_only_with_external_trace():
    x=bibliography_verify({'task_id':'T1','references':[{'reference_id':'L3','claimed':{'title':'A Valid Paper','year':2024,'doi':'10.1/abc'},'resolved':{'resolver':'crossref','title':'A Valid Paper','year':2024,'doi':'10.1/abc','source_url':'https://doi.org/10.1/abc','resolver_record_id':'10.1/abc'},'evidence_roles':['clinical_background']}]})
    assert x['references'][0]['verification_status']=='VERIFIED'
    assert x['references'][0]['external_trace_present'] is True

from modules.cohort.build_task_cohort import build as cohort_build
from modules.foundation_models.resolve_visual_fm import resolve as fm_resolve
from modules.features.validate_h5_feature_store import validate as feature_validate
from modules.artifacts.state import register as artifact_register, audit as artifact_audit


def test_execution_permission_dual_gate():
    x=resolve('TASK_SPECIFIED','ASSESS_ONLY','READY_TO_RUN')
    assert x['intent_gate']['status']=='BLOCKED'
    assert x['readiness_gate']['status']=='PASS'
    assert x['allowed'] is False
    y=resolve('TASK_SPECIFIED','EXECUTE','CONDITIONAL_READY')
    assert y['intent_gate']['status']=='PASS'
    assert y['readiness_gate']['status']=='CONDITIONAL'
    assert y['allowed'] is False


def test_cohort_builder_tcga_binary_mapping(tmp_path):
    slides=tmp_path/'slides'; slides.mkdir()
    for name in ['TCGA-AA-0001-01Z-00-DX1.svs','TCGA-AA-0002-01Z-00-DX1.svs','TCGA-AA-0003-01Z-00-DX1.svs']:
        (slides/name).write_bytes(b'')
    clinical=tmp_path/'clinical.tsv'
    pd.DataFrame({'case_submitter_id':['TCGA-AA-0001','TCGA-AA-0002','TCGA-AA-0003'],'primary_diagnosis':['Ductal','Lobular','Rare']}).to_csv(clinical,sep='\t',index=False)
    cfg={'slides':{'root':str(slides),'extensions':['.svs'],'patient_parser':'tcga_patient'},'labels':{'table':str(clinical),'sep':'\t','patient_col':'case_submitter_id','label_col':'primary_diagnosis','mapping':{'Ductal':'ductal','Lobular':'lobular'},'exclude_unmapped':True}}
    out,exc,s=cohort_build(cfg)
    assert s['patients_included']==2
    assert set(out['label'])=={'ductal','lobular'}
    assert len(exc)==1


def test_visual_fm_resolver_requires_local_or_explicit_remote(tmp_path):
    reg={'patch_encoders':{'uni_v2':{'display_name':'UNI2','embedding_dim':1536,'trident':{'patch_encoder':'uni_v2','patch_size':256,'magnification':20},'access':'gated','license':'x'}}}
    local={'resources':{'foundation_models':{'uni_v2':{'checkpoint':str(tmp_path/'missing.pt'),'access_verified':False}}}}
    x=fm_resolve(reg,local,['uni_v2'],False)
    assert x['status']=='NOT_READY'
    ck=tmp_path/'uni.pt'; ck.write_bytes(b'x')
    local['resources']['foundation_models']['uni_v2']['checkpoint']=str(ck)
    y=fm_resolve(reg,local,['uni_v2'],False)
    assert y['status']=='READY' and y['selected']['status']=='AVAILABLE_LOCAL'


def test_feature_qc_detects_complete_store(tmp_path):
    import h5py, numpy as np
    root=tmp_path/'features'; root.mkdir()
    cohort=pd.DataFrame({'slide_id':['s1','s2'],'patient_id':['p1','p2'],'label_id':[0,1],'split':['train','test']})
    cfp=tmp_path/'cohort.csv'; cohort.to_csv(cfp,index=False)
    for sid in ['s1','s2']:
        with h5py.File(root/f'{sid}.h5','w') as f:
            f.create_dataset('features',data=np.ones((4,8),dtype='float32')); f.create_dataset('coords',data=np.zeros((4,2),dtype='int32'))
    q=feature_validate(root,cfp,expected_dim=8)
    assert q['status']=='PASS' and q['coverage']==1.0


def test_artifact_staleness_detects_changed_upstream(tmp_path):
    a=tmp_path/'a.yaml'; b=tmp_path/'b.yaml'; a.write_text('x: 1'); b.write_text('y: 2')
    ra=artifact_register('a',a,{},'test'); rb=artifact_register('b',b,{'a_input':a},'test'); rb['artifact_dependencies']=['a']
    manifest={'artifacts':{'a':ra,'b':rb}}
    a.write_text('x: 9')
    z=artifact_audit(manifest)
    assert z['artifacts']['a']['state']=='STALE'
    assert z['artifacts']['b']['state']=='STALE'


def test_patient_mil_smoke_cpu(tmp_path):
    import h5py, numpy as np, subprocess, json
    root=tmp_path/'f'; root.mkdir()
    rows=[]
    # 12 patients, both classes represented in each split
    specs=[('train',8),('val',2),('test',2)]
    idx=0
    for split,n in specs:
        for j in range(n):
            y=j%2; pid=f'p{idx:02d}'; sid=f's{idx:02d}'; idx+=1
            x=np.random.default_rng(idx).normal(loc=float(y),scale=.2,size=(12,16)).astype('float32')
            with h5py.File(root/f'{sid}.h5','w') as f: f.create_dataset('features',data=x)
            rows.append({'patient_id':pid,'slide_id':sid,'label_id':y,'split':split})
    cfp=tmp_path/'cohort.csv'; pd.DataFrame(rows).to_csv(cfp,index=False)
    out=tmp_path/'run'
    cmd=[sys.executable,str(ROOT/'adapters/mil/train_patient_mil.py'),'--cohort',str(cfp),'--feature-root',str(root),'--baseline','abmil','--epochs','2','--patience','2','--hidden-dim','16','--attn-dim','8','--max-patches-per-slide','12','--device','cpu','--output-dir',str(out)]
    p=__import__('subprocess').run(cmd,capture_output=True,text=True)
    assert p.returncode==0, p.stderr
    assert (out/'metrics.json').exists()

from adapters.trident.run_contract import run as run_trident_contract

def test_full_trident_requires_sanity_pass():
    c={'commands':{'full':{'cwd':'.','argv':['echo','x']}}}; p={'final_permission':{'allowed':True}}
    assert run_trident_contract(c,'full',p,False,None)['status']=='BLOCKED_SANITY'
    assert run_trident_contract(c,'full',p,False,{'status':'PASS'})['status']=='DRY_RUN'

from modules.clinical_covariates.build_covariate_contract import build_contract as covariate_contract_build


def test_covariate_contract_rejects_target_leakage_and_ids():
    df=pd.DataFrame({
        'patient_id':['p1','p2','p3','p4'],
        'age_at_diagnosis':[50,60,55,70],
        'ajcc_pathologic_stage':['II','III','II','I'],
        'histologic_type':['ductal','lobular','ductal','lobular'],
        'case_barcode':['a','b','c','d']
    })
    c=covariate_contract_build(df,'patient_id',target_cols=['histologic_type'])
    accepted={x['column'] for x in c['accepted_covariates']}
    rejected={x['column']:x['reason'] for x in c['rejected_covariates']}
    assert {'age_at_diagnosis','ajcc_pathologic_stage'} <= accepted
    assert rejected['histologic_type']=='TARGET_COLUMN'
    assert rejected['case_barcode']=='IDENTIFIER_LIKE'
    assert c['preprocessing_contract']['fit_scope']=='TRAIN_ONLY'


def test_multimodal_smoke_cpu(tmp_path):
    import h5py, numpy as np, subprocess, json
    root=tmp_path/'features'; root.mkdir()
    rows=[]; clin=[]; idx=0
    specs=[('train',12),('val',4),('test',4)]
    for split,n in specs:
        for j in range(n):
            y=j%2; pid=f'p{idx:02d}'; sid=f's{idx:02d}'; idx+=1
            x=np.random.default_rng(idx).normal(loc=float(y),scale=.5,size=(8,12)).astype('float32')
            with h5py.File(root/f'{sid}.h5','w') as f: f.create_dataset('features',data=x)
            rows.append({'patient_id':pid,'slide_id':sid,'label_id':y,'split':split})
            clin.append({'pid':pid,'age':45+10*y+(idx%5),'stage':'III' if y else 'I'})
    cohort=tmp_path/'cohort.csv'; pd.DataFrame(rows).to_csv(cohort,index=False)
    clinical=tmp_path/'clinical.csv'; pd.DataFrame(clin).to_csv(clinical,index=False)
    contract=covariate_contract_build(pd.DataFrame(clin),'pid',requested_cols=['age','stage'])
    cpath=tmp_path/'contract.yaml'; cpath.write_text(yaml.safe_dump(contract,sort_keys=False))
    out=tmp_path/'mm'
    cmd=[sys.executable,str(ROOT/'adapters/multimodal/train_patient_multimodal.py'),'--cohort',str(cohort),'--feature-root',str(root),'--clinical-table',str(clinical),'--covariate-contract',str(cpath),'--output-dir',str(out)]
    p=subprocess.run(cmd,capture_output=True,text=True)
    assert p.returncode==0, p.stderr
    meta=json.loads((out/'metrics.json').read_text())
    assert meta['status']=='PASS'
    assert meta['preprocessing_fit_scope']=='TRAIN_ONLY'
    assert set(meta['models'])=={'pathology_only','clinical_only','concat_fusion','late_fusion'}
    assert (out/'preprocessing_provenance.yaml').exists()

from modules.evaluation.build_evaluation_contract import build as eval_contract_build
from modules.evaluation.evaluate_predictions import evaluate as evaluate_predictions
from modules.robustness.build_subgroup_report import build as subgroup_build
from modules.reproducibility.build_experiment_manifest import build as repro_build
from modules.claims.guard_clinical_claims import guard as claim_guard


def test_v04_evaluation_contract_smoke_is_diagnostic_only():
    c=eval_contract_build('classification','patient','SMOKE_INTERNAL','concat_fusion',['pathology_only','clinical_only'])
    assert c['diagnostic_only'] is True
    assert 'auroc' in c['metrics']['primary_metrics']
    assert c['rules']['smoke_metrics_are_performance_claims'] is False


def test_v04_evaluation_bootstrap_and_paired_delta(tmp_path):
    rows=[]
    y=[0,1,0,1,0,1,0,1]
    p_good=[.1,.9,.2,.8,.15,.85,.3,.7]
    p_bad=[.45,.55,.6,.4,.4,.6,.55,.45]
    for i,(yy,a,b) in enumerate(zip(y,p_good,p_bad)):
        rows.append({'patient_id':f'p{i}','label_id':yy,'split':'test',
                     'concat_fusion_prob_1':a,'pathology_only_prob_1':b})
    pred=tmp_path/'pred.csv'; pd.DataFrame(rows).to_csv(pred,index=False)
    c=eval_contract_build('classification','patient','INTERNAL_HOLDOUT','concat_fusion',['pathology_only'])
    r=evaluate_predictions(pred,c,'test',100,7)
    assert r['status']=='SCIENTIFIC_EVALUATION_READY'
    assert r['per_model']['concat_fusion']['point']['auroc'] > r['per_model']['pathology_only']['point']['auroc']
    assert r['per_model']['concat_fusion']['bootstrap']['valid_replicates'] > 0
    assert 'concat_fusion_vs_pathology_only' in r['paired_comparisons']


def test_v04_subgroup_small_groups_are_not_overinterpreted(tmp_path):
    pred=tmp_path/'p.csv'; clin=tmp_path/'c.csv'
    pd.DataFrame([
      {'patient_id':'p1','label_id':0,'split':'test','concat_fusion_prob_1':.2},
      {'patient_id':'p2','label_id':1,'split':'test','concat_fusion_prob_1':.8},
    ]).to_csv(pred,index=False)
    pd.DataFrame([{'pid':'p1','race':'A'},{'pid':'p2','race':'B'}]).to_csv(clin,index=False)
    r=subgroup_build(pred,clin,'pid',['race'],'concat_fusion','test',20)
    assert r['subgroups']['race']['groups']['A']['status']=='INSUFFICIENT_GROUP_SIZE'
    assert r['subgroups']['race']['groups']['B']['status']=='INSUFFICIENT_GROUP_SIZE'


def test_v04_claim_guard_blocks_smoke_performance_claims():
    r=claim_guard('SMOKE_INTERNAL','DIAGNOSTIC_ONLY')
    assert r['maximum_claim_level']=='EXECUTION_ONLY'
    assert 'performance' in r['forbidden_claim_classes']
    r2=claim_guard('INTERNAL_HOLDOUT','SCIENTIFIC_EVALUATION_READY')
    assert r2['maximum_claim_level']=='RETROSPECTIVE_INTERNAL_VALIDATION'
    assert 'clinical_utility' in r2['forbidden_claim_classes']


def test_v04_reproducibility_manifest_hashes_inputs_outputs(tmp_path):
    a=tmp_path/'a.txt'; b=tmp_path/'b.txt'; a.write_text('a'); b.write_text('b')
    r=repro_build('T001','SMOKE_INTERNAL',[a],[b],ROOT,42)
    assert r['status']=='FROZEN'
    assert r['inputs']['a.txt']['sha256']
    assert r['outputs']['b.txt']['sha256']
    assert r['environment']['python']


def test_v04_covariate_contract_train_aware_and_availability():
    df=pd.DataFrame({
      'pid':['p1','p2','p3','p4'],
      'age':[50,60,70,80],
      'stage':['II','II','III','IV'],
      'post_treatment':['x','y','z','w']
    })
    c=covariate_contract_build(df,'pid',requested_cols=['age','stage','post_treatment'],fit_patient_ids=['p1','p2'],availability_overrides={'age':'AVAILABLE','stage':'CONDITIONAL','post_treatment':'UNAVAILABLE'})
    acc={x['column'] for x in c['accepted_covariates']}; rej={x['column']:x['reason'] for x in c['rejected_covariates']}
    assert c['assessment_scope']=='TRAIN_ONLY'
    assert 'age' in acc
    assert rej['stage']=='CONSTANT_OR_EMPTY_IN_ASSESSMENT_SET'
    assert rej['post_treatment']=='UNAVAILABLE_AT_INFERENCE'


def test_v04_validation_runner_smoke(tmp_path):
    pred=tmp_path/'predictions.csv'; clin=tmp_path/'clinical.csv'; out=tmp_path/'v04'
    rows=[]
    for i,(y,p) in enumerate([(0,.1),(1,.9),(0,.2),(1,.8)]):
        rows.append({'patient_id':f'p{i}','label_id':y,'split':'test','pathology_only_prob_1':p,'clinical_only_prob_1':1-p,'concat_fusion_prob_1':p,'late_fusion_prob_1':.5})
    pd.DataFrame(rows).to_csv(pred,index=False)
    pd.DataFrame([{'pid':f'p{i}','race':'A' if i<2 else 'B'} for i in range(4)]).to_csv(clin,index=False)
    cmd=[sys.executable,str(ROOT/'scripts/run_v04_validation.py'),'--task-id','T001','--predictions',str(pred),'--clinical-table',str(clin),'--patient-id-col','pid','--subgroups','race','--primary-model','concat_fusion','--comparators','pathology_only','clinical_only','--study-scope','SMOKE_INTERNAL','--bootstrap-reps','20','--min-group-n','20','--skill-root',str(ROOT),'--output-dir',str(out)]
    p=subprocess.run(cmd,capture_output=True,text=True)
    assert p.returncode==0, p.stderr
    s=yaml.safe_load((out/'v04_validation_summary.yaml').read_text())
    assert s['status']=='PASS' and s['evaluation_status']=='DIAGNOSTIC_ONLY' and s['claim_level']=='EXECUTION_ONLY'
    assert (out/'reproducibility_manifest.yaml').exists()


from modules.study.build_cohort_registry import build as cohort_registry_build
from modules.study.assess_cohort_compatibility import assess as cohort_compatibility_assess
from modules.study.plan_multicohort_study import plan as multicohort_plan
from modules.export.redact_public_manifest import redact as public_redact
from modules.runs.build_run_manifest import build as run_manifest_build


def test_v1_router_recognizes_multicohort():
    r=route({'cohorts':[{'name':'A'},{'name':'B'}],'requested_tasks':[]})
    assert r['cohort_mode']=='MULTI_COHORT' and r['cohort_count']==2


def test_v1_cohort_registry_keeps_cohorts_separate():
    reg=cohort_registry_build([
      {'cohort_id':'A','name':'A','disease_context':'breast cancer','patient_identity_key':'patient_id','modalities':['WSI'],'labels':[{'target':'HER2','level':'patient'}]},
      {'cohort_id':'B','name':'B','disease_context':'breast cancer','patient_identity_key':'case_id','modalities':['WSI'],'labels':[{'target':'HER2','level':'patient'}]},
    ])
    assert reg['cohort_count']==2
    assert {x['patient_identity_key'] for x in reg['cohorts']}=={'patient_id','case_id'}
    assert reg['default_pooling_policy'].startswith('DO_NOT_POOL')


def test_v1_compatibility_blocks_prediction_level_mismatch():
    reg=cohort_registry_build([
      {'cohort_id':'A','disease_context':'breast cancer','patient_identity_key':'pid','modalities':['WSI'],'labels':[{'target':'HER2','level':'patient'}]},
      {'cohort_id':'B','disease_context':'breast cancer','patient_identity_key':'pid','modalities':['WSI'],'labels':[{'target':'HER2','level':'slide'}]},
    ])
    x=cohort_compatibility_assess(reg['cohorts'][0],reg['cohorts'][1],'HER2',['WSI'])
    assert x['status']=='INCOMPATIBLE'
    assert 'prediction_level_mismatch' in x['blockers']
    assert x['pooling_allowed'] is False


def test_v1_pooling_requires_explicit_permission():
    reg=cohort_registry_build([
      {'cohort_id':'A','disease_context':'breast cancer','patient_identity_key':'pid','modalities':['WSI'],'labels':[{'target':'HER2','level':'patient'}]},
      {'cohort_id':'B','disease_context':'breast cancer','patient_identity_key':'pid','modalities':['WSI'],'labels':[{'target':'HER2','level':'patient'}]},
    ])
    x=cohort_compatibility_assess(reg['cohorts'][0],reg['cohorts'][1],'HER2',['WSI'])
    assert x['status']=='COMPATIBLE' and x['pooling_allowed'] is False


def test_v1_external_validation_requires_explicit_independence():
    reg=cohort_registry_build([
      {'cohort_id':'DEV','disease_context':'breast cancer','patient_identity_key':'pid','modalities':['WSI'],'declared_role':'DEVELOPMENT','labels':[{'target':'HER2','level':'patient'}]},
      {'cohort_id':'CAND','disease_context':'breast cancer','patient_identity_key':'pid','modalities':['WSI'],'labels':[{'target':'HER2','level':'patient'}]},
      {'cohort_id':'EXT','disease_context':'breast cancer','patient_identity_key':'pid','modalities':['WSI'],'independence_from_development':'EXTERNAL','labels':[{'target':'HER2','level':'patient'}]},
    ])
    p=multicohort_plan(reg,'HER2',['WSI'])
    roles={x['cohort_id']:x['role'] for x in p['assignments']}
    assert roles['DEV']=='DEVELOPMENT'
    assert roles['CAND']=='VALIDATION_CANDIDATE'
    assert roles['EXT']=='EXTERNAL_VALIDATION'


def test_v1_handoff_ready_requires_scientific_frozen_contract():
    task={'task_id':'T1','target':'HER2','label_definition':'binary','clinical_question':'Can H&E predict HER2?','prediction_level':'patient','task_family':'classification'}
    split={'test_manifest':'test.csv'}
    ev={'task_family':'classification','prediction_level':'patient','study_scope':'INTERNAL_HOLDOUT'}
    repro={'status':'FROZEN'}
    h=handoff_build(task,split,{'encoder':'UNI2'},{'ABMIL':{'auroc':0.8}}, {'maximum_claim_level':'RETROSPECTIVE_INTERNAL_VALIDATION'}, evaluation_contract=ev,reproducibility_manifest=repro,artifact_state={'all_fresh':True})
    assert h['status']=='READY_FOR_AUTORESEARCH'
    assert h['readiness_reasons']==[]
    assert 'frozen_test_split' in h['immutable']
    assert 'test_set_access_rule' in h['free']


def test_v1_handoff_blocks_stale_artifacts():
    task={'task_id':'T1','target':'HER2','clinical_question':'q','prediction_level':'patient','task_family':'classification'}
    h=handoff_build(task,{'test_manifest':'test.csv'},{'encoder':'UNI2'},{'ABMIL':{'auroc':0.8}}, {'maximum_claim_level':'RETROSPECTIVE_INTERNAL_VALIDATION'}, evaluation_contract={'x':1},reproducibility_manifest={'status':'FROZEN'},artifact_state={'all_fresh':False})
    assert h['status']=='NOT_READY'
    assert 'stale_upstream_artifacts' in h['readiness_reasons']


def test_v1_public_export_redacts_absolute_paths():
    x=public_redact({'data':{'path':'/private/project/data.csv','sha256':'abc'},'checkpoint':'/models/x.pt'},{'/private/project':'<DATA_ROOT>'})
    assert x['data']['path']=='<DATA_ROOT>/data.csv'
    assert x['checkpoint'].startswith('<LOCAL_PATH>/')
    assert x['data']['sha256']=='abc'
    assert x['public_export']['absolute_paths_redacted'] is True


def test_v1_run_manifest_records_skill_version(tmp_path):
    r=run_manifest_build(ROOT,notes=['test'])
    assert r['version']=='ClinicalRunManifest-v1'
    assert r['skill']['version']=='1.0.0'
    assert r['stability_contract']['stale_artifacts_must_not_be_used_as_current_evidence'] is True


def test_v1_workspace_creates_cohort_registry(tmp_path):
    req=tmp_path/'request.yaml'; ws=tmp_path/'ws'
    req.write_text(yaml.safe_dump({'cohorts':[{'cohort_id':'A','name':'A','disease_context':'breast cancer','patient_identity_key':'pid','modalities':['WSI'],'labels':[{'target':'HER2','level':'patient'}]}],'requested_tasks':[]}))
    p=subprocess.run([sys.executable,str(ROOT/'scripts/create_workspace.py'),str(req),str(ws)],capture_output=True,text=True)
    assert p.returncode==0, p.stderr
    reg=yaml.safe_load((ws/'shared'/'cohort_registry.yaml').read_text())
    assert reg['cohort_count']==1
    assert (ws/'runs').exists() and (ws/'exports').exists()

def test_v1_finalization_runner_emits_ready_handoff(tmp_path):
    files={
      'task.yaml': {'task_id':'T001','target':'HER2','clinical_question':'Can H&E predict HER2?','label_definition':'binary','prediction_level':'patient','task_family':'classification'},
      'split.yaml': {'test_manifest':'frozen_test.csv'},
      'representation.yaml': {'encoder':'UNI2','preprocessing_hash':'abc'},
      'baselines.yaml': {'ABMIL':{'auroc':0.8}},
      'claim.yaml': {'maximum_claim_level':'RETROSPECTIVE_INTERNAL_VALIDATION'},
      'eval.yaml': {'task_family':'classification','prediction_level':'patient','study_scope':'INTERNAL_HOLDOUT'},
      'repro.yaml': {'status':'FROZEN'},
      'state.yaml': {'all_fresh':True,'artifacts':{}},
    }
    paths={}
    for name,obj in files.items():
        p=tmp_path/name; p.write_text(yaml.safe_dump(obj)); paths[name]=p
    out=tmp_path/'final'
    cmd=[sys.executable,str(ROOT/'scripts/finalize_v1_clinical_run.py'),
         '--task-spec',str(paths['task.yaml']),'--split-spec',str(paths['split.yaml']),
         '--representation',str(paths['representation.yaml']),'--baselines',str(paths['baselines.yaml']),
         '--claim-scope',str(paths['claim.yaml']),'--evaluation-contract',str(paths['eval.yaml']),
         '--reproducibility-manifest',str(paths['repro.yaml']),'--artifact-state',str(paths['state.yaml']),
         '--skill-root',str(ROOT),'--output-dir',str(out)]
    p=subprocess.run(cmd,capture_output=True,text=True)
    assert p.returncode==0, p.stderr
    h=yaml.safe_load((out/'autoresearch_handoff.yaml').read_text())
    s=yaml.safe_load((out/'v1_finalization_summary.yaml').read_text())
    assert h['status']=='READY_FOR_AUTORESEARCH'
    assert s['clinical_workflow_status']=='STABLE_CONTRACT_EMITTED'
    assert (out/'clinical_run_manifest.yaml').exists()
