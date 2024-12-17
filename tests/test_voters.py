import pytest
from wake.testing import *
from wake.testing.fuzzing import *
from pytypes.contracts.D21 import D21


def deploy_fresh_contract():
    """Deploy contract and return it with 9 fresh accounts for testing"""
    deployer = default_chain.accounts[0]
    contract = D21.deploy(from_=deployer)
    test_accounts = [default_chain.accounts[i] for i in range(1, 10)]
    return contract, test_accounts


# Tests basic voter registration
@default_chain.connect()
def test_add_voter():
    contract, accounts = deploy_fresh_contract()
    voter = accounts[0]
    
    tx = contract.addVoter(voter.address, from_=contract.owner())
    
    assert contract.voters(voter.address) == True, "Voter was not added successfully"
    assert len(tx.events) == 1
    assert tx.events[0].voter == voter.address


# Tests that only owner can add voters
@default_chain.connect()
def test_add_voter_not_owner():
    contract, accounts = deploy_fresh_contract()
    non_owner, voter = accounts[:2]
    
    with pytest.raises(Exception, match="Not the owner"):
        contract.addVoter(voter.address, from_=non_owner)


# Tests voting start functionality and its requirements
@default_chain.connect()
def test_start_voting():
    contract, accounts = deploy_fresh_contract()
    subject = accounts[0]
    
    tx_subject = contract.addSubject("Subject A", from_=subject)
    assert len(tx_subject.events) == 1
    assert tx_subject.events[0].addr == subject.address
    
    tx_start = contract.startVoting(from_=contract.owner())
    assert len(tx_start.events) == 1
    
    assert contract.votingStarted() == True, "Voting was not started"
    assert contract.votingEndTime() > 0, "Voting end time was not set"


# Tests that voting cannot start without subjects
@default_chain.connect()
def test_start_voting_no_subjects():
    contract, _ = deploy_fresh_contract()
    
    with pytest.raises(Exception, match="No subjects registered"):
        contract.startVoting(from_=contract.owner())


# Tests positive vote functionality
@default_chain.connect()
def test_vote_positive():
    contract, accounts = deploy_fresh_contract()
    subject, voter = accounts[:2]
    
    contract.addSubject("Subject A", from_=subject)
    contract.addVoter(voter.address, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    tx = contract.votePositive(subject.address, from_=voter)
    
    assert len(tx.events) == 1
    assert tx.events[0].voter == voter.address
    assert tx.events[0].subject == subject.address
    
    subject_info = contract.getSubject(subject.address)
    assert subject_info.votes == 1, "Positive vote was not counted"


# Tests positive vote limit enforcement
@default_chain.connect()
def test_vote_positive_limit():
    contract, accounts = deploy_fresh_contract()
    subjects = accounts[:4]
    voter = accounts[4]
    
    for i, subject in enumerate(subjects):
        contract.addSubject(f"Subject {i}", from_=subject)
    
    contract.addVoter(voter, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    # Cast three positive votes
    for subject in subjects[:3]:
        contract.votePositive(subject, from_=voter)
    
    with pytest.raises(Exception, match="Already cast three positive votes"):
        contract.votePositive(subjects[3], from_=voter)


# Tests negative vote functionality and requirements
@default_chain.connect()
def test_vote_negative():
    contract, accounts = deploy_fresh_contract()
    subjects = accounts[:3]
    voter = accounts[3]
    
    for i, subject in enumerate(subjects):
        contract.addSubject(f"Subject {i}", from_=subject)
    
    contract.addVoter(voter.address, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    # Cast two positive votes first
    contract.votePositive(subjects[0].address, from_=voter)
    contract.votePositive(subjects[1].address, from_=voter)
    
    # Cast negative vote
    tx_neg = contract.voteNegative(subjects[2].address, from_=voter)
    
    assert len(tx_neg.events) == 1
    assert tx_neg.events[0].voter == voter.address
    assert tx_neg.events[0].subject == subjects[2].address
    
    subject_info = contract.getSubject(subjects[2].address)
    assert subject_info.votes == -1, "Negative vote was not counted"


# Tests negative vote requires two positive votes first
@default_chain.connect()
def test_vote_negative_without_positives():
    contract, accounts = deploy_fresh_contract()
    subject, voter = accounts[:2]
    
    contract.addSubject("Subject A", from_=subject)
    contract.addVoter(voter, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    with pytest.raises(Exception, match="Need 2 positive votes first"):
        contract.voteNegative(subject, from_=voter)


# Tests remaining voting time calculation
@default_chain.connect()
def test_get_remaining_time():
    contract, accounts = deploy_fresh_contract()
    subject = accounts[0]
    
    contract.addSubject("Subject A", from_=subject)
    contract.startVoting(from_=contract.owner())
    
    remaining_time = contract.getRemainingTime()
    assert remaining_time > 0 and remaining_time <= 4 * 24 * 60 * 60, "Remaining time is incorrect"


# Tests result retrieval and vote counting
@default_chain.connect()
def test_get_results():
    contract, accounts = deploy_fresh_contract()
    subjects = accounts[:3]
    voters = accounts[3:5]
    
    # Register subjects
    for i, subject in enumerate(subjects):
        contract.addSubject(f"Subject {chr(65+i)}", from_=subject)
    
    # Add voters
    for voter in voters:
        contract.addVoter(voter.address, from_=contract.owner())
    
    contract.startVoting(from_=contract.owner())
    
    # First voter: all positive votes
    for subject in subjects[:2]:
        contract.votePositive(subject.address, from_=voters[0])
    
    contract.votePositive(subjects[2].address, from_=voters[0])
    contract.votePositive(subjects[2].address, from_=voters[1])
    
    # End voting period
    default_chain.mine(timestamp_change=lambda t: t + 4 * 24 * 60 * 60 + 1)
    
    results = contract.getResults()
    assert len(results) == 3, "Incorrect number of results"
    
    # Verify results order and votes
    assert results[0].name == "Subject C" and results[0].votes == 2
    assert results[1].name == "Subject A" and results[1].votes == 1
    assert results[2].name == "Subject B" and results[2].votes == 1


# Tests voting requires active period
@default_chain.connect()
def test_voting_not_active():
    contract, accounts = deploy_fresh_contract()
    subject, voter = accounts[:2]
    
    contract.addSubject("Subject A", from_=subject)
    contract.addVoter(voter, from_=contract.owner())
    
    with pytest.raises(Exception, match="Voting has not started"):
        contract.votePositive(subject, from_=voter)


# Tests voting period end restriction
@default_chain.connect()
def test_voting_ended():
    contract, accounts = deploy_fresh_contract()
    subject, voter = accounts[:2]
    
    contract.addSubject("Subject A", from_=subject)
    contract.addVoter(voter.address, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    default_chain.mine(timestamp_change=lambda t: t + 4 * 24 * 60 * 60 + 1)
    
    with pytest.raises(Exception, match="Voting has ended"):
        contract.votePositive(subject.address, from_=voter)


# Tests batch voting functionality
@default_chain.connect()
def test_batch_voting():
    contract, accounts = deploy_fresh_contract()
    subjects = accounts[:3]
    voter = accounts[3]
    
    for i, subject in enumerate(subjects):
        contract.addSubject(f"Subject {i}", from_=subject)
    
    contract.addVoter(voter.address, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    tx = contract.voteBatch(
        [s.address for s in subjects],
        [True, True, False],
        from_=voter
    )
    
    assert len(tx.events) == 3
    for i, event in enumerate(tx.events):
        assert event.voter == voter.address
        assert event.subject == subjects[i].address
    
    default_chain.mine(timestamp_change=lambda t: t + 4 * 24 * 60 * 60 + 1)
    
    results = contract.getResults()
    assert len(results) == 3
    assert results[0].votes == 1  # First subject
    assert results[1].votes == 1  # Second subject
    assert results[2].votes == -1  # Third subject


# Tests batch voting validations
@default_chain.connect()
def test_batch_voting_invalid():
    contract, accounts = deploy_fresh_contract()
    subjects = accounts[:2]
    voter = accounts[2]
    
    for i, subject in enumerate(subjects):
        contract.addSubject(f"Subject {i}", from_=subject)
    
    contract.addVoter(voter.address, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    with pytest.raises(Exception, match="Already voted for this subject"):
        contract.voteBatch(
            [subjects[0].address, subjects[0].address],
            [True, True],
            from_=voter
        )

    with pytest.raises(Exception, match="Need 2 positive votes first"):
        contract.voteBatch(
            [subjects[0].address],
            [False],
            from_=voter
        )


# Tests complete voting process with events
@default_chain.connect()
def test_full_voting_flow_with_events():
    contract, accounts = deploy_fresh_contract()
    owner = contract.owner()
    subjects = accounts[:3]
    voters = accounts[3:5]
    
    # Register subjects with events check
    for i, subject in enumerate(subjects):
        tx = contract.addSubject(f"Party {chr(65+i)}", from_=subject)
        assert len(tx.events) == 1
        assert tx.events[0].addr == subject.address
        assert tx.events[0].name == f"Party {chr(65+i)}"
    
    # Register voters with events check
    for voter in voters:
        tx = contract.addVoter(voter.address, from_=owner)
        assert len(tx.events) == 1
        assert tx.events[0].voter == voter.address
    
    tx_start = contract.startVoting(from_=owner)
    assert len(tx_start.events) == 1
    
    # First voter casts all positive votes
    for subject in subjects:
        tx = contract.votePositive(subject.address, from_=voters[0])
        assert contract.hasVoterVotedForSubject(voters[0].address, subject.address)
    
    # Second voter: two positive, one negative
    contract.votePositive(subjects[0].address, from_=voters[1])
    contract.votePositive(subjects[1].address, from_=voters[1])
    contract.voteNegative(subjects[2].address, from_=voters[1])
    
    default_chain.mine(timestamp_change=lambda t: t + 4 * 24 * 60 * 60 + 1)
    
    results = contract.getResults()
    assert results[0].name == "Party A" and results[0].votes == 2
    assert results[1].name == "Party B" and results[1].votes == 2
    assert results[2].name == "Party C" and results[2].votes == 0


# Tests result ordering logic
@default_chain.connect()
def test_results_ordering():
    contract, accounts = deploy_fresh_contract()
    subjects = accounts[:5]
    voters = accounts[5:8]
    
    # Register 5 subjects
    for i, subject in enumerate(subjects):
        contract.addSubject(f"Subject {i+1}", from_=subject)
    
    # Register 3 voters
    for voter in voters:
        contract.addVoter(voter.address, from_=contract.owner())
    
    contract.startVoting(from_=contract.owner())
    
    # Create varied voting pattern
    # First subject: 3 positive votes
    for voter in voters:
        contract.votePositive(subjects[0].address, from_=voter)
    
    # Second subject: 2 positive votes
    contract.votePositive(subjects[1].address, from_=voters[0])
    contract.votePositive(subjects[1].address, from_=voters[1])
    
    # Third subject: 1 positive vote
    contract.votePositive(subjects[2].address, from_=voters[0])
    
    # Fourth subject: 1 negative vote
    contract.voteNegative(subjects[3].address, from_=voters[0])
    
    # Fifth subject: no votes
    
    default_chain.mine(timestamp_change=lambda t: t + 4 * 24 * 60 * 60 + 1)
    
    results = contract.getResults()
    assert len(results) == 5
    
    # Verify order: most votes to least, zero votes before negative
    assert results[0].name == "Subject 1" and results[0].votes == 3
    assert results[1].name == "Subject 2" and results[1].votes == 2
    assert results[2].name == "Subject 3" and results[2].votes == 1
    assert results[3].name == "Subject 5" and results[3].votes == 0
    assert results[4].name == "Subject 4" and results[4].votes == -1


# Tests result access timing restrictions
@default_chain.connect()
def test_results_access_timing():
    contract, accounts = deploy_fresh_contract()
    subject, voter = accounts[:2]
    
    contract.addSubject("Test Subject", from_=subject)
    contract.addVoter(voter.address, from_=contract.owner())
    contract.startVoting(from_=contract.owner())
    
    contract.votePositive(subject.address, from_=voter)
    
    # Check result access at different times
    with pytest.raises(Exception, match="Voting hasn't ended yet"):
        contract.getResults()
    
    # After 2 days
    default_chain.mine(timestamp_change=lambda t: t + 2 * 24 * 60 * 60)
    with pytest.raises(Exception, match="Voting hasn't ended yet"):
        contract.getResults()
    
    # Just before end
    default_chain.mine(timestamp_change=lambda t: t + 2 * 24 * 60 * 60 - 1)
    with pytest.raises(Exception, match="Voting hasn't ended yet"):
        contract.getResults()
    
    # Finally after voting period
    default_chain.mine(timestamp_change=lambda t: t + 2)
    
    results = contract.getResults()
    assert len(results) == 1
    assert results[0].name == "Test Subject" and results[0].votes == 1