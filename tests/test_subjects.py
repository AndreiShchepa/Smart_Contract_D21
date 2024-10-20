import pytest
from wake.testing import *
from wake.testing.fuzzing import *
from pytypes.contracts.D21 import D21


def deploy_contract():
    return D21.deploy(from_=random_account())

@default_chain.connect()
def test_add_subject():
    contract = deploy_contract()
    subject_name = "Subject A"
    contract.addSubject(subject_name, from_=contract.owner())
    
    subjects = contract.getSubjects()
    assert len(subjects) == 1, "Subject registration failed."

@default_chain.connect()
def test_add_duplicated_subject():
    contract = deploy_contract()
    subject_name = "Subject B"
    contract.addSubject(subject_name, from_=contract.owner())

    with pytest.raises(Exception, match="Address already registered as a subject"):
        contract.addSubject(subject_name, from_=contract.owner())

    with pytest.raises(Exception, match="Address already registered as a subject"):
        contract.addSubject('Subject D', from_=contract.owner())

    a = default_chain.accounts[1]
    with pytest.raises(Exception, match="Subject name already exists"):
        contract.addSubject(subject_name, from_=a)

@default_chain.connect()
def test_get_subject_details():
    contract = deploy_contract()
    subject_name = "Subject C"
    contract.addSubject(subject_name, from_=contract.owner())

    subject_c = contract.getSubject(contract.owner())
    assert subject_c.name == 'Subject C', "Getting subject failed."
    
    a = default_chain.accounts[2]
    subject_a = contract.getSubject(contract.address, from_=a)
    assert subject_a.name == '' and subject_a.votes == 0, "Getting empty subject failed"
