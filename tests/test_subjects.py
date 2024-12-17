import pytest
from wake.testing import *
from wake.testing.fuzzing import *
from pytypes.contracts.D21 import D21

def deploy_fresh_contract():
    """Deploy contract and return it with 9 fresh accounts for testing"""
    deployer = default_chain.accounts[0]
    contract = D21.deploy(from_=deployer)
    test_accounts = [default_chain.accounts[i] for i in range(1, 10)]  # 9 accounts for tests
    return contract, test_accounts

def is_subject_added_event(event):
    """Check if event is SubjectAdded type"""
    return hasattr(event, 'name') and hasattr(event, 'addr')

# Tests basic subject registration functionality
@default_chain.connect()
def test_add_subject():
    contract, _ = deploy_fresh_contract()
    subject_name = "Subject A"
    contract.addSubject(subject_name, from_=contract.owner())
    
    subjects = contract.getSubjects()
    assert len(subjects) == 1, "Subject registration failed."

# Tests duplicate subject registration prevention and proper error handling
@default_chain.connect()
def test_add_duplicated_subject():
    contract, accounts = deploy_fresh_contract()
    subject_name = "Subject B"
    contract.addSubject(subject_name, from_=contract.owner())

    with pytest.raises(Exception, match="Address already registered as a subject"):
        contract.addSubject(subject_name, from_=contract.owner())

    with pytest.raises(Exception, match="Address already registered as a subject"):
        contract.addSubject('Subject D', from_=contract.owner())

    with pytest.raises(Exception, match="Subject name already exists"):
        contract.addSubject(subject_name, from_=accounts[0])

# Tests retrieval of subject details and handling of non-existent subjects
@default_chain.connect()
def test_get_subject_details():
    contract, accounts = deploy_fresh_contract()
    subject_name = "Subject C"
    contract.addSubject(subject_name, from_=contract.owner())

    subject_c = contract.getSubject(contract.owner())
    assert subject_c.name == 'Subject C', "Getting subject failed."
    
    subject_a = contract.getSubject(contract.address, from_=accounts[0])
    assert subject_a.name == '' and subject_a.votes == 0, "Getting empty subject failed"

# Tests event emission during the voting process
@default_chain.connect()
def test_voting_events():
    contract, accounts = deploy_fresh_contract()
    owner = contract.owner()
    voter = accounts[0]
    subjects = accounts[1:4]  # Get 3 accounts for subjects

    # Add subjects and verify events
    for i, subject in enumerate(subjects):
        tx = contract.addSubject(f"Test Subject {i+1}", from_=subject)
        assert len(tx.events) == 1
        assert tx.events[0].addr == subject.address
        
    # Add voter and start voting
    tx_voter = contract.addVoter(voter.address, from_=owner)
    assert len(tx_voter.events) == 1
    assert tx_voter.events[0].voter == voter.address
    
    tx_start = contract.startVoting(from_=owner)
    assert len(tx_start.events) == 1
    
    # Test positive votes
    for subject in subjects[:2]:
        tx_pos = contract.votePositive(subject.address, from_=voter)
        assert len(tx_pos.events) == 1
        pos_event = tx_pos.events[0]
        assert pos_event.voter == voter.address
        assert pos_event.subject == subject.address
    
    # Test negative vote
    tx_neg = contract.voteNegative(subjects[2].address, from_=voter)
    assert len(tx_neg.events) == 1
    neg_event = tx_neg.events[0]
    assert neg_event.voter == voter.address
    assert neg_event.subject == subjects[2].address

# Tests error handling when voting for non-existent subjects
@default_chain.connect()
def test_vote_for_nonexistent_subject():
    contract, accounts = deploy_fresh_contract()
    owner = contract.owner()
    voter, non_existent_subject, valid_subject = accounts[:3]

    contract.addSubject("Valid Subject", from_=valid_subject)
    contract.addVoter(voter.address, from_=owner)
    contract.startVoting(from_=owner)
    
    with pytest.raises(Exception, match="Subject not found"):
        contract.votePositive(non_existent_subject.address, from_=voter)

# Tests batch voting functionality and event emissions
@default_chain.connect()
def test_batch_voting_events():
    contract, accounts = deploy_fresh_contract()
    owner = contract.owner()
    voter = accounts[0]
    subjects = accounts[1:3]  # Get 2 accounts for subjects
    
    for i, subject in enumerate(subjects):
        tx = contract.addSubject(f"Subject {i}", from_=subject)
        assert len(tx.events) == 1
        assert tx.events[0].addr == subject.address
    
    contract.addVoter(voter.address, from_=owner)
    contract.startVoting(from_=owner)
    
    tx_batch = contract.voteBatch(
        [s.address for s in subjects],
        [True, True],
        from_=voter
    )
    
    assert len(tx_batch.events) == 2
    for i, event in enumerate(tx_batch.events):
        assert event.voter == voter.address
        assert event.subject == subjects[i].address

# Tests proper event type identification
@default_chain.connect()
def test_event_types():
    contract, accounts = deploy_fresh_contract()
    subject = accounts[0]
    
    tx = contract.addSubject("Test Subject", from_=subject)
    assert len(tx.events) == 1
    assert is_subject_added_event(tx.events[0]), "Wrong event type emitted"