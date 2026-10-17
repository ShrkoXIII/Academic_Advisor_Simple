"""Finalize new experiment evidence and render its report without model fitting."""
import hashlib
import json
from pathlib import Path
import pandas as pd
import numpy as np
from src import paths

def finalize(evidence,modeldir,metadata):
    from .runner import write_json
    from .report import render
    root=paths.PROJECT_ROOT
    manifest=json.loads(paths.SHORTLIST_MANIFEST_PATH.read_text(encoding='utf-8')) if hasattr(paths,'SHORTLIST_MANIFEST_PATH') else json.loads((root/'models/shortlist_v2/manifest.json').read_text(encoding='utf-8'))
    for stage,family in metadata['families'].items():
        size=family['model_size_bytes']
        size.setdefault('baseline_replica',size['baseline'])
        size['baseline']={role:(root/manifest['stages'][stage]['models'][role]['path']).stat().st_size for role in ('grade','fail')}
    before=json.loads((evidence/'protected_before.json').read_text(encoding='utf-8'))
    metadata['input_and_production_source_sha256']={name:sha for name,sha in before.items() if name.startswith('src/') or name in {
        'data/raw/v_acs_grade.parquet','models/shortlist_v2/manifest.json','models/model_metadata_v2.json',
        'data/artifacts/category_levels_v2.json','data/temporal/temporal_train_roster_v2.parquet','data/temporal/temporal_test_roster_v2.parquet',
        'data/processed/student_course_v2.parquet'}}
    metadata['experiment_source_sha256']={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    metadata['experiment_model_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in modeldir.iterdir() if p.is_file()}
    for input_path in [paths.TEMPORAL_TRAIN_ROSTER_PATH_V2,paths.TEMPORAL_TEST_ROSTER_PATH_V2,paths.CLEAN_STUDENT_COURSE_PATH_V2]:
        name=input_path.relative_to(root).as_posix()
        metadata['input_and_production_source_sha256'][name]=before[name]
    metadata['verification']={}
    status=Path(__file__).parent/'test_status.json'
    if status.exists(): metadata['test_status']=json.loads(status.read_text(encoding='utf-8'))
    for name in ('focused_tests','related_tests','full_tests'):
        log=Path(__file__).parent/(name+'.log')
        if log.exists(): metadata['verification'][name]={'log':log.relative_to(root).as_posix(),'tail':log.read_text(encoding='utf-8',errors='replace').splitlines()[-12:]}
    terms=['attempt_sum','course_history_avg_attempt','plan_credit_weighted_avg_attempt','peer_credit_weighted_avg_attempt']
    audit=[]
    for directory in ('src','scripts','tests'):
        for source in (root/directory).rglob('*.py'):
            if 'attempt_sum_removal' in source.parts: continue
            for number,line in enumerate(source.read_text(encoding='utf-8-sig',errors='replace').splitlines(),1):
                if any(term in line for term in terms): audit.append({'path':source.relative_to(root).as_posix(),'line':number,'text':line.strip()})
    write_json(evidence/'dependency_audit.json',audit)
    saved=root/'data/evaluation/plan_gpa_course_predictions_2025_v2.parquet'
    current=pd.read_parquet(evidence/'stage2_baseline_courses.parquet')
    if saved.exists():
        historical=pd.read_parquet(saved)
        paired=current.merge(historical,on='student_course_id',suffixes=('_fresh','_saved'),validate='one_to_one')
        if len(paired)!=len(current) or len(paired)!=len(historical): raise ValueError('Saved prediction row identities differ')
        columns=[c for c in ('predicted_mark','predicted_points','points_error') if c in current and c in historical]
        differences={c:float(np.max(np.abs(paired[c+'_fresh']-paired[c+'_saved']))) for c in columns}
        if not columns or max(differences.values())>1e-10: raise ValueError('Saved official predictions not reproduced')
        metadata['saved_evaluation_prediction_verification']={'path':saved.relative_to(root).as_posix(),'rows':len(paired),'max_absolute_difference':differences}
    else: metadata['saved_evaluation_prediction_verification']='UNVERIFIED: missing saved predictions'
    write_json(evidence/'metadata.json',metadata)
    destination=root/'reports/attempt_sum_removal_experiment.md'
    verification='\n\n### تحقق الاختبارات\n\n'
    verification+='```json\n'+json.dumps(metadata.get('test_status',{}),ensure_ascii=False,indent=2)+'\n```\n\n'
    for name,result in metadata['verification'].items():
        verification+=f"`{name}`: [{result['log']}](<{(root/result['log']).as_posix()}>)\n\n```text\n"+'\n'.join(result['tail'])+'\n```\n\n'
    with destination.open('x',encoding='utf-8') as stream: stream.write(render(evidence,modeldir,root)+verification)

if __name__=='__main__':
    evidence=paths.PROJECT_ROOT/'data/evaluation/experiments/attempt_sum_removal'
    models=paths.PROJECT_ROOT/'models/experiments/attempt_sum_removal'
    finalize(evidence,models,json.loads((evidence/'metadata.json').read_text(encoding='utf-8')))
