# Binary Search Trees (BST) 🌳

## Overview
A **Binary Search Tree** is a node-based binary tree data structure with the following properties:
- The left subtree of a node contains only nodes with keys lesser than the node's key.
- The right subtree of a node contains only nodes with keys greater than the node's key.
- The left and right subtrees each must also be a binary search tree.

## Inorder Traversal
An inorder traversal of a BST produces elements in **sorted ascending order**:

```python
def inorder(root):
    return inorder(root.left) + [root.val] + inorder(root.right) if root else []
```

## Key Complexity
- Search / Insert / Delete Average: $O(\log n)$
- Worst Case (degenerate skewed tree): $O(n)$
- Balance Solution: AVL Trees or Red-Black Trees
