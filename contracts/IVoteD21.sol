// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

struct Subject {
    string name;
    int256 votes;
}

interface IVoteD21 {
    // Add a new subject into the voting system using the name.
    function addSubject(string memory name) external;

    // Add a new voter into the voting system.
    function addVoter(address addr) external;

    // Get addresses of all registered subjects.
    function getSubjects() external view returns(address[] memory);

    // Get the subject details.
    function getSubject(address addr) external view returns(Subject memory);

    // Start the voting period.
    function startVoting() external;

    // Vote positive for the subject.
    function votePositive(address addr) external;

    // Vote negative for the subject.
    function voteNegative(address addr) external;

    // Get the remaining time to the voting end in seconds.
    function getRemainingTime() external view returns(uint256);

    // Get the voting results, sorted descending by votes.
    function getResults() external view returns(Subject[] memory);
}