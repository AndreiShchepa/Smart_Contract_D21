import pytest
from wake.testing import *
from wake.testing.fuzzing import *
from pytypes.contracts.D21 import D21

def deploy_contract():
    return D21.deploy(from_=random_account())

@default_chain.connect()
def test_add_voter():
    contract = deploy_contract()
    voter = default_chain.accounts[1]
    
    contract.addVoter(voter, from_=contract.owner())
    assert contract.voters(voter) == True, "Voter was not added successfully"

@default_chain.connect()
def test_add_voter_not_owner():
    contract = deploy_contract()
    non_owner = default_chain.accounts[1]
    voter = default_chain.accounts[2]
    
    with pytest.raises(Exception, match="Not the owner"):
        contract.addVoter(voter, from_=non_owner)

@default_chain.connect()
def test_start_voting():
    contract = deploy_contract()
    subject = default_chain.accounts[1]
    
    contract.addSubject("Subject A", from_=subject)
    contract.startVoting(from_=contract.owner())
    
    assert contract.votingStarted() == True, "Voting was not started"
    assert contract.votingEndTime() > 0, "Voting end time was not set"

@default_chain.connect()
def test_start_voting_no_subjects():
    contract = deploy_contract()
    
    with pytest.raises(Exception, match="No subjects registered"):
        contract.startVoting(from_=contract.owner())

@default_chain.connect()
def test_vote_positive():
    contract = deploy_contract()
    subject = default_chain.accounts[1]
    voter = default_chain.accounts[2]
    
    contract.addSubject("Subject A", from_=subject)
    contract.addVoter(voter, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    contract.votePositive(subject, from_=voter)
    
    subject_info = contract.getSubject(subject)
    assert subject_info.votes == 1, "Positive vote was not counted"

@default_chain.connect()
def test_vote_positive_limit():
    contract = deploy_contract()
    subject1 = default_chain.accounts[1]
    subject2 = default_chain.accounts[2]
    subject3 = default_chain.accounts[3]
    voter = default_chain.accounts[4]
    
    contract.addSubject("Subject A", from_=subject1)
    contract.addSubject("Subject B", from_=subject2)
    contract.addSubject("Subject C", from_=subject3)
    contract.addVoter(voter, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    contract.votePositive(subject1, from_=voter)
    contract.votePositive(subject2, from_=voter)
    
    with pytest.raises(Exception, match="Already cast two positive votes"):
        contract.votePositive(subject3, from_=voter)

@default_chain.connect()
def test_vote_negative():
    contract = deploy_contract()
    subject1 = default_chain.accounts[1]
    subject2 = default_chain.accounts[2]
    voter = default_chain.accounts[3]
    
    contract.addSubject("Subject A", from_=subject1)
    contract.addSubject("Subject B", from_=subject2)
    contract.addVoter(voter, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    contract.votePositive(subject1, from_=voter)
    contract.votePositive(subject2, from_=voter)
    contract.voteNegative(subject1, from_=voter)
    
    subject_info = contract.getSubject(subject1)
    assert subject_info.votes == 0, "Negative vote was not counted"

@default_chain.connect()
def test_vote_negative_without_positives():
    contract = deploy_contract()
    subject = default_chain.accounts[1]
    voter = default_chain.accounts[2]
    
    contract.addSubject("Subject A", from_=subject)
    contract.addVoter(voter, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    with pytest.raises(Exception, match="Need 2 positive votes first"):
        contract.voteNegative(subject, from_=voter)

@default_chain.connect()
def test_get_remaining_time():
    contract = deploy_contract()
    subject = default_chain.accounts[1]
    
    contract.addSubject("Subject A", from_=subject)
    contract.startVoting(from_=contract.owner())
    
    remaining_time = contract.getRemainingTime()
    assert remaining_time > 0 and remaining_time <= 2 * 24 * 60 * 60, "Remaining time is incorrect"

@default_chain.connect()
def test_get_results():
    contract = deploy_contract()
    subject1 = default_chain.accounts[1]
    subject2 = default_chain.accounts[2]
    voter1 = default_chain.accounts[3]
    voter2 = default_chain.accounts[4]
    
    contract.addSubject("Subject A", from_=subject1)
    contract.addSubject("Subject B", from_=subject2)
    contract.addVoter(voter1, from_=contract.owner())
    contract.addVoter(voter2, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    # Voter 1 casts 2 positive votes and 1 negative
    contract.votePositive(subject1, from_=voter1)
    #print(contract.getResults())
    contract.votePositive(subject2, from_=voter1)
    #print(contract.getResults())
    contract.voteNegative(subject2, from_=voter1)
    #print(contract.getResults())

    # Voter 2 casts 2 positive votes
    contract.votePositive(subject1, from_=voter2)
    contract.votePositive(subject2, from_=voter2)
    
    results = contract.getResults()
    assert len(results) == 2, "Incorrect number of results"

    assert results[0].name == "Subject A", f"Incorrect name for Subject A: {results[0].name}"
    assert results[1].name == "Subject B", f"Incorrect name for Subject B: {results[1].name}"
    
    # Update these assertions based on the actual output
    assert results[0].votes == 2, f"Incorrect result for Subject A: {results[0].votes}"
    assert results[1].votes == 1, f"Incorrect result for Subject B: {results[1].votes}"

@default_chain.connect()
def test_voting_not_active():
    contract = deploy_contract()
    subject = default_chain.accounts[1]
    voter = default_chain.accounts[2]
    
    contract.addSubject("Subject A", from_=subject)
    contract.addVoter(voter, from_=contract.owner())
    
    with pytest.raises(Exception, match="Voting has not started"):
        contract.votePositive(subject, from_=voter)

@default_chain.connect()
def test_voting_ended():
    contract = deploy_contract()
    subject = default_chain.accounts[1]
    voter = default_chain.accounts[2]
    
    contract.addSubject("Subject A", from_=subject)
    contract.addVoter(voter, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    # Define a function to advance time by 3 days
    def advance_time(current_timestamp: int) -> int:
        return current_timestamp + 3 * 24 * 60 * 60

    # Advance time by 3 days
    default_chain.mine(timestamp_change=advance_time)
    
    with pytest.raises(Exception, match="Voting has ended"):
        contract.votePositive(subject, from_=voter)