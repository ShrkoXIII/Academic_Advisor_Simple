"""Verify every fit artifact against executed source, rows, config and feature order."""
import json
import lightgbm as lgb
from src import paths
from src.features.frozen_history import file_sha256
from .workflow import (OUTPUT, MODELS, HERE, load_train, row_fingerprint, feature_subset,
                       configuration_signature, validate_signature, learn_category_levels,
                       verify_protected, write_json)


def run():
    setup=json.loads((OUTPUT/'setup.json').read_text())
    archive=HERE/'evidence/executed_workflow.py'
    if file_sha256(archive)!=setup['workflow_sha256']:
        raise ValueError('Executed source archive differs from recorded workflow')
    for relative,digest in setup['sources'].items():
        if file_sha256(paths.PROJECT_ROOT/relative)!=digest:
            raise ValueError('Executed input changed')
    train=load_train()
    results=[]
    for year in [2023,2024]:
        fit=train[train.part_id.le((year-1)*10+3)]
        valid=train[train.part_id.between(year*10+1,year*10+3)]
        fit_hash,valid_hash=row_fingerprint(fit),row_fingerprint(valid)
        levels=learn_category_levels(fit)
        for spec in setup['specs']:
            folder=MODELS/str(year)/spec['name']
            if json.loads((folder/'categories.json').read_text())!=levels:
                raise ValueError('Wrong training-only categories')
            selected=json.loads((OUTPUT/str(year)/spec['name']/'inner_selection.json').read_text())['selected']
            config={'parameters':selected['parameters'],'rounds':selected['rounds']}
            for variant in setup['variants']:
                features=feature_subset(spec['features'],variant)
                signature=configuration_signature({'run':setup['signature'],'year':year,'spec':spec,
                    'variant':variant,'features':features,'config':config,
                    'fit_rows':fit_hash,'valid_rows':valid_hash})
                model_path=folder/f'{variant}.txt'
                record=json.loads(model_path.with_suffix('.json').read_text())
                validate_signature(record['signature'],signature)
                if file_sha256(model_path)!=record['sha256'] or record['features']!=features or record['configuration']!=config:
                    raise ValueError('Experimental model evidence changed')
                if lgb.Booster(model_file=str(model_path)).feature_name()!=features:
                    raise ValueError('Model input feature order mismatch')
                results.append({'year':year,'model':spec['name'],'variant':variant,'sha256':record['sha256'],
                                'signature':signature,'feature_count':len(features)})
    if len(results)!=108:
        raise ValueError('Missing outer model artifacts')
    protection=verify_protected()
    write_json(OUTPUT/'artifact_integrity.json',{'status':'PASS','models_verified':len(results),
        'executed_source_sha256':file_sha256(archive),'executed_source_archive':archive.relative_to(paths.PROJECT_ROOT).as_posix(),
        'current_runner_sha256':file_sha256(HERE/'workflow.py'),'runner_hardened_after_numerical_fits':True,
        'old_cache_reuse_rejected':True,'protection':protection,'models':results})
    print('Verified',len(results),'models; executed source; exact categories/configurations/rows; protected files unchanged')


if __name__=='__main__':
    run()
