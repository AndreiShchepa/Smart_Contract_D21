// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

struct Subject {
    string name;
    int256 votes;
}

interface IVoteD21 {
    event VotingStarted();
    event VoterAdded(address indexed voter);
    event SubjectAdded(address indexed addr, string name);
    event PositiveVoted(address indexed voter, address indexed subject);
    event NegativeVoted(address indexed voter, address indexed subject);
    
    // Add a new subject into the voting system using the name
    function addSubject(string memory name) external;

    // Get addresses of all registered subjects
    function getSubjects() external view returns(address[] memory);

    // Get the subject details
    function getSubject(address addr_) external view returns(Subject memory);

    // Add a new voter into the voting system
    function addVoter(address voter_) external;

    // Start the voting period
    function startVoting() external;

    // Vote positive for the subject
    function votePositive(address subject_) external;

    // Vote negative for the subject
    function voteNegative(address subject_) external;

    // Vote for multiple subjects
    function voteBatch(address[] calldata subjects_, bool[] calldata votes_) external;

    // Get the remaining time to the voting end in seconds
    function getRemainingTime() external view returns(uint256);

    // Get the voting results, sorted descending by votes
    function getResults() external view returns(Subject[] memory);
}